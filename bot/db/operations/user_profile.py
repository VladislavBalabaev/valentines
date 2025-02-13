import logging
from aiogram import types
from functools import wraps
from datetime import datetime

from create_bot import bot
from db.operations.utils.conversion import user_conversion
from db.operations.users import update_user, find_all_users
from db.operations.utils.mongo_errors import MongoDBUserNotFound
from db.connect import get_mongo_users, get_mongo_messages, get_mongo_matches


async def create_user(message: types.Message):
    """
    Creates a new user in the MongoDB 'users' and 'messages' collections with the initial structure.
    """
    mongo_users = get_mongo_users()
    mongo_messages = get_mongo_messages()

    user_id = message.from_user.id

    user_structure = {
        "_id": user_id,
        "info": {
            "time_registred": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chat_id": message.chat.id,
            "email": "",
            "full_name": message.from_user.full_name,           # his name in tg
            "username": message.from_user.username,             # his tg tag
            "written_name": "",                                 # what was written in tg bot by user in /start
            "age": "",
            "program": {
                "name": "",
                "year": "",
            },
            "sex": "",
            "partner_sex": "",
            "about": "",
        },
        "survey": {
            "question1": "",
            "question2": "",
            "question3": "",
            "question4": "",
            "question5": "",
            "question6": "",
            "question7": "",
            "question8": "",
            "question9": "",
            "question10": "",
            "finished": "no",
        },
        "partner_survey": {
            "question1": "",
            "question2": "",
            "question3": "",
            "question4": "",
            "question5": "",
            "question6": "",
            "question7": "",
            "question8": "",
            "question9": "",
            "question10": "",
            "finished": "no",
        },
        "blacklist": [],                                        # of user_ids
        "blocked_bot": "no",
        "finished_profile": "no",
        "blocked_matching": "no",
        "cache": {},
    }

    messages_structure = {
        "_id": user_id,
        "messages": [],
    }

    await mongo_users.insert_one(user_structure)
    await mongo_messages.insert_one(messages_structure)

    username = await user_conversion.get(user_id)
    logging.info(f"_id={user_id:<10} {username} <> was added to DB")

    return


def new_user(f):
    """
    Decorator that creates a new user in MongoDB if the user does not exist.
    """
    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            await f(*args, **kwargs)
        except MongoDBUserNotFound:    
            message = None
            for arg in args:
                if isinstance(arg, types.Message):
                    message = arg
                    break
            message = kwargs.get("message", message)

            await create_user(message)

            await f(*args, **kwargs)

    return wrapper


async def delete_everithing():
    """
    Deletes all entries from the 'users', 'messages', and 'matches' collections in MongoDB.
    """
    mongo_users = get_mongo_users()
    mongo_messages = get_mongo_messages()
    mongo_matches = get_mongo_matches()

    await mongo_users.delete_many({})
    await mongo_messages.delete_many({})
    await mongo_matches.delete_many({})

    return


async def actualize_user(user_id: int):
    """
    Updates the user's profile with their latest username and full name, and marks whether they have blocked the bot.
    """
    try:
        user: types.User = await bot.get_chat(user_id)
    except Exception as e:
        if "Forbidden" in str(e):
            await update_user(user_id, {"blocked_bot": "yes"})
        else:
            logging.exception(f"\nERROR: [Error retrieving chat for user {user_id}]\nTRACEBACK:")
        
        return

    await update_user(user_id, {
        "info.username": user.username,
        "info.full_name": user.full_name,
        "blocked_bot": "no",
        }
    )

    return


async def actualize_all_users():
    """
    Updates the profile information for all users who have active matching enabled.
    """
    users = await find_all_users(["_id", "blocked_bot", "active_matching"])

    for user in users:
        if user["active_matching"] == "yes":
            await actualize_user(user["_id"])

    return
