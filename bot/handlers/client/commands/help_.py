from aiogram import types, Router
from aiogram.filters.command import Command
from aiogram.filters.state import StateFilter

from handlers.common.checks import checker
from db.operations.messages import send_msg_user


router = Router()


@router.message(StateFilter(None), Command("help"))
@checker
async def cmd_help(message: types.Message):
    """
    Handles the /help command, providing users with information on available commands 
    and how to use the bot's features, including profile management and blacklist control.
    """
    await send_msg_user(message.from_user.id, 
                        "Ты можешь открыть Menu, там находятся все доступные тебе команды\n\nЕсли хочешь создать (если еще не создан) или обновить профиль, напиши /start.\nПосмотреть черный список, добавить в него или исключить из, выбери /blacklist.")
    await send_msg_user(message.from_user.id, 
                        "Если еще остались вопросы, не стесняйся, пиши @vbalab и/или @Madfyre, обязательно тебе поможем!")

    return
