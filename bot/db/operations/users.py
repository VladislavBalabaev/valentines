import logging

from db.connect import get_mongo_users, get_mongo_messages
from db.operations.utils.conversion import user_conversion


async def update_user(user_id: int, keys_values: dict):
    """
    Updates the specified keys and values for a user in the MongoDB 'users' collection.
    Logs the changes made.
    """
    mongo_users = get_mongo_users()

    filter = {"_id": user_id}
    newvalues = { "$set": keys_values}

    await mongo_users.update_one(filter, newvalues)

    username = await user_conversion.get(user_id)
    logging.info(f"_id={user_id:<10} {username} <> {list(newvalues['$set'].keys())} were updated in DB.")

    return


async def find_user(user_id: int, keys: list = []):
    """
    Retrieves a user from the MongoDB 'users' collection based on user ID.
    Specific fields can be retrieved by providing keys.
    """
    mongo_users = get_mongo_users()

    keys = {k: 1 for k in keys}

    if keys:
        user = await mongo_users.find_one({"_id": user_id}, keys)
    else:
        user = await mongo_users.find_one({"_id": user_id})

    return user


async def find_all_users(keys: list = []):
    """
    Retrieves all users from the MongoDB 'users' collection.
    Specific fields can be retrieved by providing keys.
    """
    mongo_users = get_mongo_users()

    keys = {k: 1 for k in keys}

    if keys:
        users_cursor = mongo_users.find({}, keys)
    else:
        users_cursor = mongo_users.find()

    users = await users_cursor.to_list(length=None)

    return users


async def delete_user(user_id: int):
    """
    Deletes a user from the MongoDB 'users' collection based on user ID.
    """
    mongo_users = get_mongo_users()
    mongo_messages = get_mongo_messages()
    
    await mongo_users.delete_one({"_id": user_id})
    await mongo_messages.delete_one({"_id": user_id})

    return


async def find_id_by_username(username: str):
    """
    Finds a user's ID based on their username from the MongoDB 'users' collection.
    """
    mongo_users = get_mongo_users()

    user = await mongo_users.find_one({"info.username": username}, 
                                      {"_id": 1, "info.username": 1})

    try:
        return user["_id"]
    except:
        return None


async def blacklist_add(user_id: int, username):
    """
    Adds a username to the user's blacklist in the MongoDB 'users' collection.
    Returns False if the user is already in the blacklist.
    """
    blacklist = await find_user(user_id, ["blacklist"])
    blacklist = blacklist["blacklist"]

    if username in blacklist:
        return False

    blacklist.append(username)

    await update_user(user_id, {"blacklist": blacklist})

    return True


async def blacklist_remove(user_id: int, username):
    """
    Removes a username from the user's blacklist in the MongoDB 'users' collection.
    Returns False if the username is not in the blacklist.
    """
    blacklist = await find_user(user_id, ["blacklist"])
    blacklist = blacklist["blacklist"]

    try:
        blacklist.remove(username)        
    except Exception:
        return False

    await update_user(user_id, {"blacklist": blacklist})

    return True
