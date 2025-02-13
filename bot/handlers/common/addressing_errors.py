import logging
import traceback
from aiogram import types
from functools import wraps
from aiogram.fsm.context import FSMContext

from db.operations.messages import send_msg_user
from handlers.admin.send_on import send_to_admins


async def error_occured(message: types.Message, state: FSMContext, error: Exception):
    """
    Handles an error by logging the traceback, notifying the user, and sending the error details to admins.
    """
    try:
            
        if state is not None:
            state = await state.get_state()

        logging.exception(f"\nERROR: {error}\nTRACEBACK:")

        await send_msg_user(message.from_user.id, 
                            "Извини, что-то пошло не так(\nМы уже получили ошибку, разберемся!\n\nЕсли долго не чиним, можешь написать @Madfyre и/или @vbalab по поводу бота.",
                            fail=True)

        tb_message = ''.join(traceback.format_exception(type(error), error, error.__traceback__))

        await send_to_admins(
            f"Error, check the logs.\n"
            f"User: @{message.from_user.username}.\n"
            f"State: {state}.\n"
            f"Message: \"{message.text}\".\n"
            "----------\n\n"
            f"{error.__class__.__name__}: {error}\n\n"
            f"{tb_message}"
        )

    except Exception:
        if message.from_user.username is None:
            await message.answer("Данным ботом могут пользоваться только зарегестрированные в телеграм пользователи.\nЗарегестрируйся в телеграм, чтобы у тебя появился свой @tg и приходи, будем ждать)")
        else:
            await message.answer("Возникла непредусмотренная ошибка, которую мы уже получили, разберемся!\n\nЕсли долго не чиним, можешь написать @vbalab и/или @Madfyre по поводу бота.")

        await send_to_admins(
            f"Error, check the logs.\n"
            f"User (NAME): @{message.from_user.first_name}.\n"
            f"State: {state}.\n"
            f"Message: \"{message.text}\".\n"
            "----------\n\n"
            f"{error.__class__.__name__}: {error}\n\n"
            f"{tb_message}"
        )


def error_sender(f):
    """
    Decorator that wraps functions to handle any exceptions. 
    If an error occurs, it sends error details to admins and logs the traceback.
    """
    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            await f(*args, **kwargs)

        except Exception as e:
            message = None
            state = None

            for arg in args:
                if isinstance(arg, types.Message):
                    message = arg
                elif isinstance(arg, FSMContext):
                    state = arg
            
            message = kwargs.get("message", message)
            state = kwargs.get("state", state)

            await error_occured(message=message, state=state, error=e)
    return wrapper
