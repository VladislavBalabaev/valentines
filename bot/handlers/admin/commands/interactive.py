import logging
from datetime import datetime
from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.command import Command, CommandObject

from handlers.common.checks import checker
from handlers.admin.matching import sending
from db.operations.messages import send_msg_user
from handlers.admin.admin_filter import AdminFilter
from handlers.admin.matching.assignment import match
from handlers.admin.matching.save import save_matching
from db.operations.user_profile import actualize_all_users
from db.operations.users import find_id_by_username, find_all_users, delete_user, update_user

router = Router()


class SendMessageStates(StatesGroup):
    """
    State management for sending a message to a specific user.
    """
    MESSAGE = State()


class SendMessageToGroupStates(StatesGroup):
    """
    State management for sending a message to group of users.
    """
    MESSAGE = State()


class SendMessageToAllStates(StatesGroup):
    """
    State management for sending a message to all users.
    """
    MESSAGE = State()


class DeleteUserStates(StatesGroup):
    """
    State management for deleting user.
    """
    CONFIRMED = State()


@router.message(StateFilter(None), Command("match"), AdminFilter())
@checker
async def cmd_match(message: types.Message):
    """
    Executes the matching process, saving the results and notifying admins and users.
    """
    time_started = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

    await actualize_all_users()
    logging.info(f"process='matching'                        !! Data of active users was actualized.")
 
    matched_df = await match()
    logging.info(f"process='matching'                        !! Users were matched; Emojis were attached.")

    await save_matching(matched_df, time_started)
    logging.info(f"process='matching'                        !! Results of matching were saved.")

    await sending.send_matching_admin(matched_df)
    logging.info(f"process='matching'                        !! Admins were notified.")

    await sending.send_matching_client(matched_df)
    logging.info(f"process='matching'                        !! Users were notified.")

    return


@router.message(StateFilter(None), Command("pseudo_match"), AdminFilter())
@checker
async def cmd_pseudo_match(message: types.Message):
    """
    Simulates the matching process and notifies admins of the results without saving them.
    """
    await actualize_all_users()
    logging.info(f"process='matching'                        !! Data of active users was actualized.")
 
    matched_df = await match()
    logging.info(f"process='matching'                        !! Users were matched; Emojis were attached.")

    await sending.send_matching_admin(matched_df)
    logging.info(f"process='matching'                        !! Admins were notified.")

    return


@router.message(StateFilter(None), Command("send_message"), AdminFilter())
@checker
async def cmd_send_message(message: types.Message, command: CommandObject, state: FSMContext):
    """
    Initiates the process to send a message to a specific user, prompting the admin for the message content.
    """
    if not command.args or len(command.args.split()) != 1:
        await send_msg_user(message.from_user.id, "Введи пользователя:\n/send_message @vbalab")
        return

    username = command.args.replace('@', '').replace(' ', '')

    user_id = await find_id_by_username(username)
    if not user_id:
        await send_msg_user(message.from_user.id, "Этот пользователь не пользуется ботом. Abort")
        return

    await state.update_data(user_id=user_id)

    await send_msg_user(message.from_user.id, "Введи сообщение")

    await state.set_state(SendMessageStates.MESSAGE)

    return


@router.message(StateFilter(SendMessageStates.MESSAGE), AdminFilter())
@checker
async def send_message_message(message: types.Message, state: FSMContext):
    """
    Sends the admin's message to the specified user and clears the state.
    """
    user_data = await state.get_data()
    user_id = user_data['user_id']

    await send_msg_user(user_id, message.text)

    await state.clear()

    return


@router.message(StateFilter(None), Command("send_message_to_group"), AdminFilter())
@checker
async def cmd_send_message_to_group(message: types.Message, command: CommandObject, state: FSMContext):
    """
    Initiates the process to send a message to a specific group of users, prompting the admin for the message content.
    """
    if not command.args or len(command.args.split(',')) <= 1:
        await send_msg_user(message.from_user.id, "Введи пользователей через запятую:\n/send_message_to_group @vbalab, @MadFyre")
        return

    usernames = command.args.replace('@', '').replace(' ', '').split(',')

    user_ids = []
    for username in usernames:
        user_id = await find_id_by_username(username)
        if not user_id:
            await send_msg_user(message.from_user.id, f"Пользователь {username} не пользуется ботом. Abort")
            return
        user_ids.append(user_id)

    await state.update_data(user_ids=user_ids)

    await send_msg_user(message.from_user.id, "Введи сообщение")

    await state.set_state(SendMessageToGroupStates.MESSAGE)

    return


@router.message(StateFilter(SendMessageToGroupStates.MESSAGE), AdminFilter())
@checker
async def send_message_to_group_message(message: types.Message, state: FSMContext):
    """
    Sends the admin's message to the specified group of users user and clears the state.
    """
    user_data = await state.get_data()
    user_ids = user_data['user_ids']

    for user_id in user_ids:
        await send_msg_user(user_id, message.text)

    await state.clear()

    return


@router.message(StateFilter(None), Command("send_message_to_all"), AdminFilter())
@checker
async def cmd_send_message_to_all(message: types.Message, state: FSMContext):
    """
    Initiates the process to send a message to all users, prompting the admin for the message content.
    """
    await send_msg_user(message.from_user.id, "Введи сообщение")

    await state.set_state(SendMessageToAllStates.MESSAGE)

    return


@router.message(StateFilter(SendMessageToAllStates.MESSAGE), AdminFilter())
@checker
async def send_message_to_all_message(message: types.Message, state: FSMContext):
    """
    Sends the admin's message to all users who have not blocked the bot and are active for matching.
    """
    users = await find_all_users(["_id", "info.username", "blocked_bot", "survey.finished", "partner_survey.finished"])

    for user in users:
        if user["blocked_bot"] == "no" and user["survey.finished"] == "yes" and user["partner_survey.finished"] == "yes":
            await send_msg_user(user["_id"], message.text)

    await state.clear()

    return


@router.message(StateFilter(None), Command("delete_user"), AdminFilter())
@checker
async def cmd_delete_user(message: types.Message, command: CommandObject, state: FSMContext):
    """
    Initiates the process to delete user, prompting the admin for confirm.
    """
    if not command.args or len(command.args.split()) != 1:
        await send_msg_user(message.from_user.id, "Введи пользователя:\n/delete_user @vbalab")
        return

    await send_msg_user(message.from_user.id, "Напиши то, что нужно, чтобы удалить этого пользователя")

    username = command.args.replace('@', '').replace(' ', '')

    user_id = await find_id_by_username(username)
    if not user_id:
        await send_msg_user(message.from_user.id, "Этот пользователь не пользуется ботом. Abort")
        return

    await state.update_data(user_id=user_id)

    await state.set_state(DeleteUserStates.CONFIRMED)

    return


@router.message(StateFilter(DeleteUserStates.CONFIRMED), AdminFilter())
@checker
async def delete_user_sure(message: types.Message, state: FSMContext):
    """
    Confirmes code and deletes user.
    """
    if message.text != "9182hdalsdj102":
        await send_msg_user(message.from_user.id, "Не верно. Обратитесь к другим админам за кодом")

        await state.clear()

        return

    user_data = await state.get_data()
    
    user_id = user_data['user_id']

    await delete_user(user_id);

    logging.info(f"process='delete_user' !! Data of user {user_id} was deleted.")

    if (message.from_user.id != user_id):
        await send_msg_user(message.from_user.id, f"Пользователь был удален.")

    await state.clear()

    return

@router.message(StateFilter(None), Command("create_user"), AdminFilter())
@checker
async def cmd_delete_user(message: types.Message, command: CommandObject, state: FSMContext):
    """
    Initiates the process to delete user, prompting the admin for confirm.
    """
    if not command.args or len(command.args.split()) != 1:
        await send_msg_user(message.from_user.id, "Введи пользователя:\n/create_user @vbalab")
        return

    username = command.args.replace('@', '').replace(' ', '')

    user_id = await find_id_by_username(username)
    if not user_id:
        await send_msg_user(message.from_user.id, "Этот пользователь не пользуется ботом. Abort")
        return
    
    await update_user(message.from_user.id, 
                    {"info.email": "fake@nes.ru", "cache": {}})

    await send_msg_user(user_id, 
                        "Твой аккаунт был зарегистрирован админами!\nНажми /start для заполнения информации о себе")

    return
