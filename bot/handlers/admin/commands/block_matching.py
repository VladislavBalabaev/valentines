import logging
from enum import Enum
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup

from handlers.common.checks import checker
from db.operations.messages import send_msg_user
from handlers.admin.admin_filter import AdminFilter
from handlers.client.shared.contains import contains_command
from handlers.client.shared.keyboard import create_reply_keyboard
from db.operations.users import find_user, update_user, find_id_by_username


router = Router()


class BlockMatchingStates(StatesGroup):
    """
    Defines the states for blocking or unblocking user matching.
    """
    DECISION = State()

    BLOCK = State()
    AFTER_BLOCK = State()

    UNBLOCK = State()
    AFTER_UNBLOCK = State()


class BlockMatchingChoice(Enum):
    """
    Enum class for blocking matching choices: add, remove, or cancel.
    """
    ADD = "Запретить мэтчинг"
    REMOVE = "Разрешить мэтчинг"
    CANCEL = "Отмена"


async def block_matching_add(username: str):
    """
    Blocks matching for a specific user based on their username. Returns False if already blocked.
    """
    user_id = await find_id_by_username(username)

    blocked_matching = await find_user(user_id, ["blocked_matching"])
    blocked_matching = blocked_matching["blocked_matching"]

    if blocked_matching == "yes":
        return False

    await update_user(user_id, {"blocked_matching": "yes"})

    return True


async def block_matching_remove(username: str):
    """
    Unblocks matching for a specific user based on their username. Returns False if already unblocked.
    """
    user_id = await find_id_by_username(username)

    blocked_matching = await find_user(user_id, ["blocked_matching"])
    blocked_matching = blocked_matching["blocked_matching"]

    if blocked_matching == "no":
        return False

    await update_user(user_id, {"blocked_matching": "no"})

    return True


@router.message(StateFilter(None), Command("block_matching"), AdminFilter())
@checker
async def cmd_block_matching(message: types.Message, state: FSMContext):
    """
    Handles the /block_matching command, prompting the admin to choose whether to block or unblock matching for a user.
    """
    keyboard = create_reply_keyboard(BlockMatchingChoice)
    await send_msg_user(message.from_user.id, 
                        "Выбери, что будем делать:", 
                        reply_markup=keyboard)

    await state.set_state(BlockMatchingStates.DECISION)


@router.message(StateFilter(BlockMatchingStates.DECISION), F.text == BlockMatchingChoice.ADD.value)
@checker
@contains_command
async def block_matching_block(message: types.Message, state: FSMContext):
    """
    Prompts the admin to enter a username to block from matching.
    """
    await send_msg_user(message.from_user.id, 
                        "Напиши, кому запретить мэтчинг (напр., @person_tg)", 
                        reply_markup=types.ReplyKeyboardRemove())

    await state.set_state(BlockMatchingStates.BLOCK)


@router.message(StateFilter(BlockMatchingStates.BLOCK))
@checker
@contains_command
async def block_matching_after_block(message: types.Message, state: FSMContext):
    """
    Blocks matching for the specified username and notifies the admin if the user is already blocked.
    """
    username = message.text.strip().replace(' ', '').replace('@', '')

    if await block_matching_add(username):
        logging.info(f"process='blocking matching'               !! User {username} has now matching blocked.")
        await send_msg_user(message.from_user.id,
                            f"Пользователь {username} теперь не будет участвовать в мэтчинге")
    else:
        await send_msg_user(message.from_user.id,
                            f"Этому пользователю мэтчинг уже был запрещен")

    await state.clear()


@router.message(StateFilter(BlockMatchingStates.DECISION), F.text == BlockMatchingChoice.REMOVE.value)
@checker
@contains_command
async def block_matching_unblock(message: types.Message, state: FSMContext):
    """
    Prompts the admin to enter a username to unblock from matching.
    """
    await send_msg_user(message.from_user.id, 
                        "Напиши, кого разрешить мэтчинг (напр., @person_tg)", 
                        reply_markup=types.ReplyKeyboardRemove())

    await state.set_state(BlockMatchingStates.UNBLOCK)


@router.message(StateFilter(BlockMatchingStates.UNBLOCK))
@checker
@contains_command
async def block_matching_after_unblock(message: types.Message, state: FSMContext):
    """
    Unblocks matching for the specified username and notifies the admin if the user is already unblocked.
    """
    username = message.text.strip().replace(' ', '').replace('@', '')

    if await block_matching_remove(username):
        logging.info(f"process='blocking matching'               !! User {username} has now matching allowed.")
        await send_msg_user(message.from_user.id,
                            f"Пользователь {username} теперь будет участвовать в мэтчинге")
    else:
        await send_msg_user(message.from_user.id,
                            f"Этому пользователю мэтчинг уже был разрешен")

    await state.clear()


@router.message(StateFilter(BlockMatchingStates.DECISION), F.text == BlockMatchingChoice.CANCEL.value)
@checker
@contains_command
async def block_matching_end(message: types.Message, state: FSMContext):
    """
    Handles the cancellation of the block/unblock matching process and clears the state.
    """
    await send_msg_user(message.from_user.id,
                        "Хорошо",
                        reply_markup=types.ReplyKeyboardRemove())

    await state.clear()


def is_invalid_block_matching_choice(message: types.Message) -> bool:
    """
    Checks if the user's input is an invalid block matching choice.
    """
    return message.text not in [choice.value for choice in BlockMatchingChoice]


@router.message(StateFilter(BlockMatchingStates.DECISION), is_invalid_block_matching_choice)
@checker
@contains_command
async def block_matching_no_command_choice(message: types.Message):
    """
    Informs the admin if an invalid choice is made during the block matching process.
    """
    keyboard = create_reply_keyboard(BlockMatchingChoice)
    await send_msg_user(message.from_user.id, 
                        "Выбери из предложенных вариантов", 
                        reply_markup=keyboard)

    return
