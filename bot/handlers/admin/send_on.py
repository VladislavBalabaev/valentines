import logging
from aiogram import types, exceptions

from create_bot import bot
from configs.logs import logs_path
from configs.selected_ids import ADMINS
from db.operations.messages import send_msg_user
from db.operations.utils.conversion import user_conversion
from db.operations.utils.mongo_errors import MongoDBUserNotFound


async def send_to_admins(text: str, doc=None):
    for admin_id in ADMINS:
        try:
            if doc:
                await bot.send_document(admin_id, document=doc, caption=text)
            else:
                await send_msg_user(admin_id, text)

        except exceptions.TelegramBadRequest:
                admin = await user_conversion.get(admin_id)
                logging.error(f"Failed to send message to {admin}: {text}")

        except MongoDBUserNotFound:
                logging.error(f"Failed to send message to {admin_id}: {text}")


async def send_startup():
    """
    Sends a startup notification to all admins and logs the startup event.
    """
    logging.info("### Bot has started working! ###")

    await send_to_admins("Bot has started working!")


async def send_shutdown():
    """
    Sends a shutdown notification and the bot's logs to all admins, and logs the shutdown event.
    """
    logging.info("### Bot has finished working! ###")

    await send_to_admins("Bot has finished working!", doc=types.FSInputFile(logs_path))
