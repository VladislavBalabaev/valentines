from aiogram import Dispatcher

from handlers.client import commands


def register_handlers_client(dp: Dispatcher):
    """
    Registers all client-related command routers, including start, blacklist, active status, and help commands.
    """
    dp.include_routers(
        commands.start.router,
        commands.survey.router,
        commands.blacklist.router,
        commands.help_.router,
    )
