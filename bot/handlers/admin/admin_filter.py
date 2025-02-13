from aiogram import types
from aiogram.filters import Filter

from configs.selected_ids import ADMINS


class AdminFilter(Filter):
    """
    A filter that checks if the message sender is an admin by verifying their user ID.
    """
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMINS
