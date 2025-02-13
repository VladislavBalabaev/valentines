import os
import json
from aiogram import types, Router
from aiogram.filters.state import StateFilter
from aiogram.filters.command import Command, CommandObject

from create_bot import bot
from configs.logs import logs_path
from configs.env_reader import TEMP_DIR
from handlers.common.checks import checker
from handlers.admin.admin_filter import AdminFilter
from db.operations.messages import send_msg_user, find_messages
from db.operations.users import find_user, find_id_by_username, find_all_users


router = Router()


async def send_temporary_file(user_id: int, text: str):
    """
    Sends a temporary text file to the user with the provided content and deletes the file after sending.
    """
    file_path = TEMP_DIR / f"user_{user_id}.txt"
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)

    await bot.send_document(user_id, document=types.FSInputFile(file_path))

    os.remove(file_path)

    return


@router.message(StateFilter(None), Command("admin"), AdminFilter())
@checker
async def cmd_admin(message: types.Message):
    """
    Sends a list of available admin commands to the user.
    """
    await send_msg_user(message.from_user.id, 
                        """/logs - текущие логи;\n\n/all_users - данные всех пользователей;\n\n/messages @tg 15 - последние N сообщений пользователя;\n\n/user @tg - данные пользователя;\n\n/send_message @tg - отправить сообщение пользователю;\n\n/send_message_to_group @tg1 @tg2 - отправить сообщение выбранным пользоватлеям;\n\n/send_message_to_all - отправить сообщение всем пользователям;\n\n/block_matching - заблокировать мэтчинг для пользователя;\n\n/delete_user @tg - удалить пользователя;\n\n/create_user @tg - создать пользователя;\n\n/pseudo_match - сделать мэтчинг;\n\n\n/match - сделать мэтчинг;""")

    return


@router.message(StateFilter(None), Command("logs"), AdminFilter())
@checker
async def cmd_logs(message: types.Message):
    """
    Sends the current log file to the admin.
    """
    await message.answer_document(types.FSInputFile(logs_path))

    return


@router.message(StateFilter(None), Command("messages"), AdminFilter())
@checker
async def cmd_messages(message: types.Message, command: CommandObject):
    """
    Retrieves and sends the last N messages of a specified user to the admin.
    If the message content is too long, it sends it as a temporary file.
    """
    if not command.args or len(command.args.split()) != 2:
        await send_msg_user(message.from_user.id, "Введи пользователя и кол-во сообщений:\n/messages @vbalab 30")
        return

    args = command.args.split()
    username = args[0].replace('@', '').replace(' ', '')
    n_messages = int(args[1])

    requested_user_id = await find_id_by_username(username)

    messages = await find_messages(requested_user_id)
    messages = messages[-n_messages:]
    messages_json = json.dumps(messages, indent=3, ensure_ascii=False)
    messages_formatted = f"<pre>{messages_json}</pre>"

    if len(messages_formatted) > 4000:
        await send_temporary_file(message.from_user.id, messages_json)
    else:
        await message.answer(messages_formatted, parse_mode="HTML")

    return


@router.message(StateFilter(None), Command("user"), AdminFilter())
@checker
async def cmd_user(message: types.Message, command: CommandObject):
    """
    Retrieves and sends the profile information of a specified user to the admin.
    """
    if not command.args or len(command.args.split()) != 1:
        await send_msg_user(message.from_user.id, "Введи пользователя:\n/user @vbalab")
        return

    username = command.args.split()[0].replace('@', '').replace(" ", '')

    user_id = await find_id_by_username(username)
    user_info = await find_user(user_id)

    user_info = json.dumps(user_info, indent=3, ensure_ascii=False)

    await message.answer(f"<pre>{user_info}</pre>", parse_mode="HTML")

    return


@router.message(StateFilter(None), Command("all_users"), AdminFilter())
@checker
async def cmd_all_users(message: types.Message):
    """
    Retrieves and sends the profile information of all users to the admin.
    If the content is too long, it sends it as a temporary file.
    """
    users = await find_all_users(["_id", "info.username", "info.email", "finished_profile", "survey.finished", "partner_survey.finished"])

    users_json = json.dumps(users, indent=3, ensure_ascii=False)
    users_formatted = f"<pre>{users_json}</pre>"

    if len(users_formatted) > 4000:
        await send_temporary_file(message.from_user.id, users_json)
    else:
        await message.answer(users_formatted, parse_mode="HTML")

    return
