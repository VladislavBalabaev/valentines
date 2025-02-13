from create_bot import bot
from handlers.common.addressing_errors import error_sender
from db.operations.messages import send_msg_user, recieve_msg_user


@error_sender
async def notify_users_with_pending_updates():
    """
    Notifies users with pending updates when the bot becomes active again. 
    Retrieves any pending updates, logs the messages, and prompts users to try again.
    """
    updates = await bot.get_updates(offset=None, timeout=1)

    notified_users = set()

    for update in updates:
        if update.message:
            user_id = update.message.from_user.id
            await recieve_msg_user(update.message, pending=True)

            if user_id not in notified_users:
                await send_msg_user(user_id,
                                    "Бот был неактивен, но сейчас еще как!\nПопробуй еще раз, пожалуйста")

                notified_users.add(user_id)

    await bot.get_updates(offset=updates[-1].update_id + 1 if updates else None)        # drop pending updates

    return
