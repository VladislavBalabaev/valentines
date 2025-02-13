from aiogram import Dispatcher

from handlers.common import commands


def register_handler_cancel(dp: Dispatcher):
    """
    Registers the handler for the /cancel command, allowing users to cancel ongoing operations.
    """
    dp.include_routers(
        commands.cancel.router,
    )


def register_handler_zero_message(dp: Dispatcher):
    """
    Registers the handler for cases when no specific command or message is recognized.
    """
    dp.include_routers(
        commands.zero_message.router,
    )
