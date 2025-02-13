import json
import logging
import pandas as pd
from aiogram import exceptions

from create_bot import bot
from configs.selected_ids import ADMINS
from db.operations.messages import send_msg_user
from handlers.admin.commands.non_interactive import send_temporary_file


async def send_matching_admin(matched: pd.DataFrame):
    """
    Sends the matching results to all admins. If the message content is too long, 
    it sends it as a temporary file.
    """
    matched_formatted = matched.drop(["info"], axis=1).T.to_dict('dict')
    matched_formatted = json.dumps(matched_formatted, indent=3, ensure_ascii=False)
    matched_formatted = f"<pre>{matched_formatted}</pre>"

    for admin in ADMINS:
        try:
                
            if len(matched_formatted) > 4000:
                await send_temporary_file(admin, matched_formatted)
            else:
                await bot.send_message(admin, matched_formatted, parse_mode="HTML")
        except exceptions.TelegramBadRequest:
            logging.error(f"Failed to send matching message to {admin}.")
    return


async def send_matching_client(matched: pd.DataFrame):
    """
    Sends the matching results to each user, providing information on who they were matched with, 
    along with their respective emoji identifiers. If no matches are found, the user is notified.
    """
    def info_by_username(username):
        """
        Formats the information of the matched user to be sent to the client.
        """
        nonlocal matched

        row = matched.loc[matched["username"] == username].iloc[0]

        return f"{row['info']['written_name']} (@{row['username']}) с {row['info']['program']['name']}'{row['info']['program']['year']}.\nСмайл пользователя - {row['emoji']}\n\nО себе: {row['info']['about']}"


    for user_id in matched.index:
        await send_msg_user(user_id, 
                            f"Привет! Пришли с результатами\n\nТвой смайл - {matched.loc[user_id, 'emoji']}")

        assignments = matched.loc[user_id, 'assignments']
        n = len(assignments)

        if n == 0:
            await send_msg_user(user_id,
                                f"В этот раз тебе не досталось тех, кому можно написать.\nВозможно, это потому что у тебя слишком много людей в черном списке.\n\nВерни кого-нибудь из него и в следующий раз шанс кого-нибудь получить будет больше")
        elif n == 1:
            await send_msg_user(user_id,
                                f"В этот раз тебе выпал только один человек, которому ты можешь написать:")

            await send_msg_user(user_id,
                                info_by_username(assignments[0]))

            await send_msg_user(user_id, 
                                "Ты можешь написать ему его смайл. Он сразу поймет, что выпал тебе на кофе)")
        elif n == 2:
            await send_msg_user(user_id,
                                info_by_username(assignments[0]))

            await send_msg_user(user_id,
                                info_by_username(assignments[1]))

            await send_msg_user(user_id,
                                f"Ты можешь написать им их смайл. Они сразу поймут, что выпали тебе на кофе)")
        else:
            raise ValueError(f"_id='{user_id}' has more than 2 assignments.")

        await send_msg_user(user_id,
                            f"Напомним, что распределение участников асимметричное.\nТо есть, те люди, которые выпали тебе, скорее всего не получили тебя")

    return
