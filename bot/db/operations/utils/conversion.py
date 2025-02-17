import re
import asyncio
import logging

from db.connect import get_mongo_users
from configs.selected_ids import ADMINS
from db.operations.utils.mongo_errors import MongoDBUserNotFound

username_id = {}
dict_lock = asyncio.Lock()


class UserConversion:
    """
    Handles the conversion of user IDs to their respective usernames with caching.
    If the user is an admin, an admin label is appended to the username.
    """
    def __init__(self) -> None:
        self.users_dict = {}
        self.dict_lock = asyncio.Lock()

    async def add(self, _id):
        """
        Retrieves a username from MongoDB for the given user ID and caches it.
        If the user is an admin, appends an admin label to the username.
        """
        mongo_users = get_mongo_users()

        username = await mongo_users.find_one({"_id": _id}, {"info.username": 1})

        try:
            username = username["info"]["username"]
        except TypeError:
            raise MongoDBUserNotFound(f"User with id {_id} is not found in MongoDB.")

        if _id in ADMINS:
            username += " \033[92m[admin]\033[0m"

        try:
            username_stripped = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]').sub('', username)
        except:
            logging.exception(f"\nERROR: [Error doing `UserConversion.add` for user with _id={_id}]")
            username = "NONE"
            username_stripped = "NONE"

        username = f"({username + ')':<{25 + len(username) - len(username_stripped)}}"

        async with self.dict_lock:
            self.users_dict[_id] = username

        return username

    async def get(self, _id):
        """
        Retrieves the cached username for a user ID or fetches it from MongoDB if not cached.
        """
        async with self.dict_lock:
            username = self.users_dict.get(_id)

        if username is None:
            username = await self.add(_id)

        return username


user_conversion = UserConversion()
