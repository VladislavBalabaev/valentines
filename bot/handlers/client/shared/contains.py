from aiogram import types
from functools import wraps

from db.operations.messages import send_msg_user


def contains_command(f):
    """
    Decorator that checks if the user input contains a command (i.e., starts with '/').
    If a command is detected, it prompts the user to cancel or retry their previous input.
    """
    @wraps(f)
    async def wrapper(*args, **kwargs):
        message = None
        for arg in args:
            if isinstance(arg, types.Message):
                message = arg
                break
        message = kwargs.get("message", message)


        if '/' == message.text[0]:
            await send_msg_user(message.from_user.id,
                                "Была введена команда\nЕсли хочешь перейти к другой команде сначала сделай /cancel.\n\nЕсли хочешь продолжить, то просто ответь заново на предыдущее сообщение")
        else:
            await f(*args, **kwargs)

    return wrapper
