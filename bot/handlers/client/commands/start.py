from enum import Enum
from random import randint
from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup

# from db.operations.user_profile import delete_everithing
from handlers.common.checks import checker
from handlers.client.email import send_email
from db.operations.messages import send_msg_user
from db.operations.users import update_user, find_user
from handlers.client.shared.contains import contains_command
from handlers.client.shared.keyboard import create_reply_keyboard


router = Router()


N_STEPS = 7;


class StartStates(StatesGroup):
    """
    State management for handling the registration process, including email verification, profile setup, 
    and program details.
    """
    EMAIL_GET = State()
    EMAIL_SET = State()
    NAME = State()
    AGE = State()
    PROGRAM_NAME = State()
    PROGRAM_YEAR = State()
    SEX = State()
    PARTNER_SEX = State()
    ABOUT = State()

class StartSexChoices(Enum):
    BOY = "парень"
    GIRL = "девушка"
    
    @classmethod
    def has_value(cls, value):
        """
        Checks if the provided value is a valid program name.
        """
        return value in cls._value2member_map_


class StartProgramNames(Enum):
    """
    Enum class representing available program names for the registration process.
    """
    BAE = "BAE"
    MAE = "MAE"
    MAF = "MAF"
    MIF = "MiF"
    MSF = "MSF"
    EDS = "EDS"
    
    @classmethod
    def has_value(cls, value):
        """
        Checks if the provided value is a valid program name.
        """
        return value in cls._value2member_map_


# @router.message(StateFilter(None), Command("d"))
# async def cmd_AAAAAA(message: types.Message, state: FSMContext):
#     await delete_everithing()


@router.message(StateFilter(None), Command("start"))
@checker
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Handles the /start command. Initiates the registration process or allows users to update their profile 
    if they have already registered.
    """
    exist = await find_user(message.from_user.id, ["info.email"])
    exist = exist["info"]["email"]

    if not exist:
        await send_msg_user(message.from_user.id, 
                            "Привет! 😊\nДобро пожаловать в бот ко Дню Святого Валентина для студентов и выпускников РЭШ.\n\nВсё очень просто:\nнужно будет пройти короткий опросник описав себя, а позже потенциального партнера.\n\nДавай начнём с регистрации, это займёт минуту!")

        await send_msg_user(message.from_user.id,
                            "Для того, чтобы подтвердить, что ты причастен к РЭШ, пожалуйста, укажи свой адрес электронной почты @nes.ru")

        await state.set_state(StartStates.EMAIL_GET)
    else:
        await send_msg_user(message.from_user.id, 
                            "Почта у тебя уже привязана, поэтому давай пройдемся по данным")

        await send_msg_user(message.from_user.id, 
                            f"[Шаг 1/{N_STEPS}]\nКак тебя зовут?")

        await state.set_state(StartStates.NAME)

    return


@router.message(StateFilter(StartStates.EMAIL_GET))
@checker
@contains_command
async def start_email_get(message: types.Message, state: FSMContext):
    """
    Collects the user's @nes.ru email address and sends a verification code if the email is valid.
    """
    if "@nes.ru" in message.text:
        await send_msg_user(message.from_user.id,
                            "Отлично, сейчас отправим тебе письмо с кодом подтверждения.\nПодожди секундочку...")

        code = str(randint(100000, 999999))

        await update_user(message.from_user.id,
                          {"cache.email": message.text, "cache.email_code": code})

        await send_email(message.text, f"Еще раз привет!\nТвой код для NEScafeBot: {code}.\nКод был отправлен для аккаунта @{message.from_user.username}")

        await send_msg_user(message.from_user.id, 
                            "Мы отправили тебе на почту код из 6 цифр.\nПожалуйста, введи его сюда")

        await state.set_state(StartStates.EMAIL_SET)
    else:
        await send_msg_user(message.from_user.id, 
                            "Это не @nes.ru адрес электронной почты 😕\n\nПожалуйста, введи правильный адрес",
                            fail=True)
    
    return


@router.message(StateFilter(StartStates.EMAIL_SET))
@checker
@contains_command
async def start_email_set(message: types.Message, state: FSMContext):
    """
    Verifies the email by checking the user's input against the sent verification code.
    """
    cache = await find_user(message.from_user.id, ["cache"])
    email_code = cache["cache"]["email_code"]

    if message.text.replace(' ', '') == email_code:
        email = cache["cache"]["email"]

        await update_user(message.from_user.id, 
                          {"info.email": email, "cache": {}})

        await send_msg_user(message.from_user.id, 
                            "Отлично!\nТвой адрес электронной почты успешно подтверждён и привязан к аккаунту\n\nТеперь давай тебя зарегистрируем в боте")

        await send_msg_user(message.from_user.id, 
                            f"[Шаг 1/{N_STEPS}]\nКак тебя зовут? 😊")

        await state.set_state(StartStates.NAME)
    else:
        await send_msg_user(message.from_user.id, 
                            "Упс, неверный код😕\nПопробуй ещё раз.\n\nP.S. Если ты случайно указал не тот адрес электронной почты, введи /cancel и начни регистрацию заново с помощью команды /start.",
                            fail=True)

    return


@router.message(StateFilter(StartStates.NAME))
@checker
@contains_command
async def start_name(message: types.Message, state: FSMContext):
    """
    Collects the user's name and moves to the next step in the registration process.
    """
    if len(message.text) < 50 and len(message.text.split(" ")) <= 3:
        await update_user(message.from_user.id, 
                          {"info.written_name": message.text})

        await send_msg_user(message.from_user.id, 
                            f"[Шаг 2/{N_STEPS}]\nСколько тебе лет?")

        await state.set_state(StartStates.AGE)
    else:
        await send_msg_user(message.from_user.id, 
                            "Кажется, это имя слишком длинное 😅",
                            fail=True)
    
    return


@router.message(StateFilter(StartStates.AGE))
@checker
@contains_command
async def start_age(message: types.Message, state: FSMContext):
    """
    Collects the user's age and verifies that it's a valid number within the acceptable range.
    """
    if message.text.isdigit() and int(message.text) >= 16 and int(message.text) <= 99:
        await update_user(message.from_user.id, 
                          {"info.age": message.text})

        keyboard = create_reply_keyboard(StartProgramNames)

        await send_msg_user(message.from_user.id,
                            f"[Шаг 3/{N_STEPS}]\nПожалуйста, выбери свою программу обучения из списка ниже\n\n(Если нет подходящей программы, выбери наиболее близкую)",
                            reply_markup=keyboard)

        await state.set_state(StartStates.PROGRAM_NAME)
    else:
        await send_msg_user(message.from_user.id, 
                            "Хмм, это не похоже на возраст 😕\n\nПожалуйста, введи свой возраст одним числом",
                            fail=True)
    
    return


@router.message(StateFilter(StartStates.PROGRAM_NAME))
@checker
@contains_command
async def start_program_name(message: types.Message, state: FSMContext):
    """
    Collects the user's program name and ensures it's a valid option from the predefined list.
    """
    program = message.text

    if StartProgramNames.has_value(program):
        await update_user(message.from_user.id, 
                          {"info.program.name": program})

        await send_msg_user(message.from_user.id,
                            f"[Шаг 4/{N_STEPS}]\nТеперь, выбери год окончания своей программы (напр., 2027)",
                            reply_markup=types.ReplyKeyboardRemove())

        await state.set_state(StartStates.PROGRAM_YEAR)
    else:
        keyboard = create_reply_keyboard(StartProgramNames)
        await send_msg_user(message.from_user.id,
                            "Пожалуйста, выбери один из предложенных вариантов 😊",
                            reply_markup=keyboard)

    return


@router.message(StateFilter(StartStates.PROGRAM_YEAR))
@checker
@contains_command
async def start_program_year(message: types.Message, state: FSMContext):
    year = message.text

    if year.isdigit() and int(year) >= 1990 and int(year) < 9999:
        await update_user(message.from_user.id, 
                          {"info.program.year": year})

        keyboard = create_reply_keyboard(StartSexChoices)

        await send_msg_user(message.from_user.id,
                            f"[Шаг 5/{N_STEPS}]\nУкажи свой пол",
                            reply_markup=keyboard)
        
        await state.set_state(StartStates.SEX)
    else:
        await send_msg_user(message.from_user.id, 
                            "Это не похоже на год окончания программы 😕\n\nПожалуйста, введи год в формате yyyy (напр., 2027)",
                            fail=True)

    return


@router.message(StateFilter(StartStates.SEX))
@checker
@contains_command
async def start_program_year(message: types.Message, state: FSMContext):
    sex = message.text

    if StartSexChoices.has_value(sex):
        await update_user(message.from_user.id, 
                          {"info.sex": sex})

        keyboard = create_reply_keyboard(StartSexChoices)

        await send_msg_user(message.from_user.id, 
                            f"[Шаг 6/{N_STEPS}]\nКакого пола ты ищешь партнера?",
                            reply_markup=keyboard)

        await state.set_state(StartStates.PARTNER_SEX)
    else:
        await send_msg_user(message.from_user.id, 
                            "Это не похоже пол бинарного человека 😕\n\nПожалуйста, введи выбери из предложенного",
                            fail=True)

    return


@router.message(StateFilter(StartStates.PARTNER_SEX))
@checker
@contains_command
async def start_program_year(message: types.Message, state: FSMContext):
    """
    Collects the user's program year and ensures it's a valid number.
    """
    partner_sex = message.text

    if StartSexChoices.has_value(partner_sex):
        await update_user(message.from_user.id, 
                          {"info.partner_sex": partner_sex})

        await send_msg_user(message.from_user.id, 
                            f"[Шаг 7/{N_STEPS}]\nРасскажи о себе в нескольких предложениях.\nЭто поможет другим участникам узнать тебя лучше.\n\nЕсли ничего не приходит на ум, ничего страшно) Ты можешь написать все что угодно, а также просто поставить прочерк.\nНаписать о себе всегда можно будет позднее",
                            reply_markup=types.ReplyKeyboardRemove())

        await state.set_state(StartStates.ABOUT)
    else:
        await send_msg_user(message.from_user.id, 
                            "Это не похоже пол бинарного человека 😕\n\nПожалуйста, введи выбери из предложенного",
                            fail=True)

    return


@router.message(StateFilter(StartStates.ABOUT))
@checker
@contains_command
async def start_about(message: types.Message, state: FSMContext):
    """
    Collects a short description from the user and finalizes the registration process.
    """
    if len(message.text) > 400:
        await send_msg_user(message.from_user.id, 
                    "Похоже, что описание слишком длинное 😅\n\nПожалуйста, попробуй написать покороче (до 300 символов)",
                    fail=True)
        return

    existed = await find_user(message.from_user.id, ["finished_profile"])
    existed = existed["finished_profile"]

    await update_user(message.from_user.id, 
                        {"info.about": message.text, 
                        "finished_profile": "yes",})

    if existed == "yes":
        await send_msg_user(message.from_user.id,
                            "Твои данные обновлены! 🎉\nТакже ты можешь перепройти опросники через /survey и /partner_survey")
    else:
        await send_msg_user(message.from_user.id,
                            "Отлично, регистрация завершена! 🎉\nЕсли захочешь изменить свои данные, сделай /start\n\nP.S. Повторно подтверждать адрес электронной почты не потребуется 😉")
        await send_msg_user(message.from_user.id, 
                            "Пройди, пожалуйста, небольшой опросник с категориями ответов, нажав на /survey.")

    await state.clear()

    return
