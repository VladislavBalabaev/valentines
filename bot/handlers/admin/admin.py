from aiogram import Dispatcher

from handlers.admin import commands


def register_handlers_admin(dp: Dispatcher):
    """
    Registers all admin-related command routers (interactive, non-interactive, and block matching).
    """
    dp.include_routers(commands.interactive.router)
    dp.include_routers(commands.non_interactive.router)
    dp.include_routers(commands.block_matching.router)
