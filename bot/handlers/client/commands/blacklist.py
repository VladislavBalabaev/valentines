from enum import Enum
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup

from db.operations.messages import send_msg_user
from handlers.client.shared.contains import contains_command
from handlers.client.shared.keyboard import create_reply_keyboard
from handlers.common.checks import checker, check_finished_profile
from db.operations.users import blacklist_add, blacklist_remove, find_user


router = Router()


class BlacklistStates(StatesGroup):
    """
    State management for adding or removing users from the blacklist.
    """
    BLACKLIST = State()
    BLOCK = State()
    AFTER_BLOCK = State()
    UNBLOCK = State()
    AFTER_UNBLOCK = State()


class BlacklistChoice(Enum):
    """
    Enum for choosing whether to add or remove users from the blacklist.
    """
    ADD = "Добавлять в ЧС"
    REMOVE = "Удалять из ЧС"
    CANCEL = "Отмена"


class BlacklistYesNo(Enum):
    """
    Enum for confirming if the user wants to continue adding or removing users.
    """
    YES = "Да"
    NO = "Нет"


@router.message(StateFilter(None), Command("blacklist"))
@checker
@check_finished_profile
async def cmd_blacklist(message: types.Message, state: FSMContext):
    """
    Handles the /blacklist command and provides options to add or remove users from the blacklist.
    Displays the current blacklist if it exists.
    """
    await send_msg_user(message.from_user.id, 
                        "Люди из черного списка не будут предлагаться тебе и ты не будешь предложен им.\n\nСейчас ты можешь добавить какого-либо конкретного человека через его @tg, а также удалить человека из черного списка, если он там находится.")

    blacklist = await find_user(message.from_user.id, ["blacklist"])
    blacklist = blacklist["blacklist"]
    if blacklist:
        blacklist = '\n'.join([f"@{user}" for user in blacklist])
        await send_msg_user(message.from_user.id,
                            f"У тебя есть пользователи в чс:\n{blacklist}")
    else:
        await send_msg_user(message.from_user.id,
                            "Пока что твой черный список пуст")

    keyboard = create_reply_keyboard(BlacklistChoice)
    await send_msg_user(message.from_user.id, 
                        "Выбери, что будем делать:", 
                        reply_markup=keyboard)

    await state.set_state(BlacklistStates.BLACKLIST)


@router.message(StateFilter(BlacklistStates.BLACKLIST), F.text == BlacklistChoice.ADD.value)
@router.message(StateFilter(BlacklistStates.AFTER_BLOCK), F.text == BlacklistYesNo.YES.value)
@checker
@contains_command
async def blacklist_block(message: types.Message, state: FSMContext):
    """
    Prompts the user to enter a username to add to the blacklist.
    """
    await send_msg_user(message.from_user.id, 
                        "Напиши, кого добавить в чс (напр., @person_tg)", 
                        reply_markup=types.ReplyKeyboardRemove())

    await state.set_state(BlacklistStates.BLOCK)


@router.message(StateFilter(BlacklistStates.BLOCK))
@checker
@contains_command
async def blacklist_after_block(message: types.Message, state: FSMContext):
    """
    Adds the specified user to the blacklist and confirms the action. 
    Prompts the user to add another user if desired.
    """
    username = message.text.strip().replace(' ', '').replace('@', '')

    if await blacklist_add(message.from_user.id, username):
        await send_msg_user(message.from_user.id,
                            f"Добавили @{username} в твой черный список.")
    else:
        await send_msg_user(message.from_user.id,
                            f"Этот пользователь уже есть в твоем черном списке")

    keyboard = create_reply_keyboard(BlacklistYesNo)
    await message.answer(
        f"Хочешь добавить @tg ещё кого-нибудь?", 
        reply_markup=keyboard
        )

    await state.set_state(BlacklistStates.AFTER_BLOCK)


@router.message(StateFilter(BlacklistStates.BLACKLIST), F.text == BlacklistChoice.REMOVE.value)
@router.message(StateFilter(BlacklistStates.AFTER_UNBLOCK), F.text == BlacklistYesNo.YES.value)
@checker
@contains_command
async def blacklist_unblock(message: types.Message, state: FSMContext):
    """
    Prompts the user to enter a username to remove from the blacklist.
    """
    await send_msg_user(message.from_user.id, 
                        "Напиши, кого исключить из чс (напр., @person_tg)", 
                        reply_markup=types.ReplyKeyboardRemove())

    await state.set_state(BlacklistStates.UNBLOCK)


@router.message(StateFilter(BlacklistStates.UNBLOCK))
@checker
@contains_command
async def blacklist_after_unblock(message: types.Message, state: FSMContext):
    """
    Removes the specified user from the blacklist and confirms the action. 
    Prompts the user to remove another user if desired.
    """
    username = message.text.strip().replace(' ', '').replace('@', '')

    if await blacklist_remove(message.from_user.id, username):
        await send_msg_user(message.from_user.id,
                            f"Исключили из твоего черного списка!")
    else:
        await send_msg_user(message.from_user.id,
                            f"Этого пользователя не было в твоем черном списке")

    keyboard = create_reply_keyboard(BlacklistYesNo)
    await send_msg_user(message.from_user.id,
                        f"Хочешь исключить из ЧС ещё чей-нибудь @tg?", 
                        reply_markup=keyboard)

    await state.set_state(BlacklistStates.AFTER_UNBLOCK)


@router.message(StateFilter(BlacklistStates.BLACKLIST), F.text == BlacklistChoice.CANCEL.value)
@router.message(StateFilter(BlacklistStates.AFTER_BLOCK), F.text == BlacklistYesNo.NO.value)
@router.message(StateFilter(BlacklistStates.AFTER_UNBLOCK), F.text == BlacklistYesNo.NO.value)
@checker
@contains_command
async def blacklist_end(message: types.Message, state: FSMContext):
    """
    Ends the blacklist modification process and displays the updated blacklist.
    """
    await send_msg_user(message.from_user.id,
                        "Хорошо",
                        reply_markup=types.ReplyKeyboardRemove())

    blacklist = await find_user(message.from_user.id, ["blacklist"])
    blacklist = blacklist["blacklist"]

    if blacklist:
        blacklist = '\n'.join([f"@{user}" for user in blacklist])
        await send_msg_user(message.from_user.id,
                            f"Твои люди в чс:\n{blacklist}")
    else:
        await send_msg_user(message.from_user.id,
                            "Твой черный список пуст")

    await state.clear()


def is_invalid_blacklist_choice(message: types.Message) -> bool:
    """
    Checks if the user input is a valid choice for the blacklist process.
    """
    return message.text not in [choice.value for choice in BlacklistChoice]


@router.message(StateFilter(BlacklistStates.BLACKLIST), is_invalid_blacklist_choice)
@checker
@contains_command
async def blacklist_no_command_choice(message: types.Message):
    """
    Informs the user to select from the available options if an invalid choice is made during the blacklist process.
    """
    keyboard = create_reply_keyboard(BlacklistChoice)
    await send_msg_user(message.from_user.id, 
                        "Выбери из предложенных вариантов", 
                        reply_markup=keyboard)

    return


def is_invalid_blacklist_yesno(message: types.Message) -> bool:
    """
    Checks if the user input is a valid yes/no choice for the blacklist process.
    """
    return message.text not in [choice.value for choice in BlacklistYesNo]


@router.message(StateFilter(BlacklistStates.AFTER_BLOCK, BlacklistStates.AFTER_UNBLOCK), is_invalid_blacklist_yesno)
@checker
@contains_command
async def blacklist_no_command_yesno(message: types.Message, state: FSMContext):
    """
    Informs the user to select from the available yes/no options if an invalid choice is made.
    """
    keyboard = create_reply_keyboard(BlacklistYesNo)
    await send_msg_user(message.from_user.id, 
                        "Выбери из предложенных вариантов", 
                        reply_markup=keyboard)

    return
