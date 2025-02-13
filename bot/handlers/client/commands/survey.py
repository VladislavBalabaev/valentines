from enum import Enum
from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import State, StatesGroup

from db.operations.users import update_user
from db.operations.messages import send_msg_user
from handlers.client.shared.contains import contains_command
from handlers.client.shared.keyboard import create_reply_keyboard
from handlers.common.checks import checker, check_finished_profile


router = Router()

SURVEY_QUESTIONS = [
    "Я открытый к общению человек",
    "Обычно я критично отношусь к другим, испытываю желание поспорить",
    "Меня можно назвать ответственным, дисциплинированным человеком",
    "Я легко расстраиваюсь и тревожусь",
    "Я многосторонний человек, открыт новому опыту",
    "В общении с людьми я стараюсь не проявлять истинные эмоции",
    "Про меня можно сказать, что я сочувствующий и добросердечный человек",
    "Мои действия скорее спонтанные, чем последовательные",
    "Я отношу себя к эмоционально стабильным и спокойным людям",
    "Можно сказать, что я консервативный, тяжело принимающий новое"
]

PARTNER_SURVEY_QUESTIONS = [
    "Это открытый к общению человек",
    "Обычно критично относится к другим, испытывает желание поспорить",
    "Можно назвать ответственным, дисциплинированным человеком",
    "Легко расстраивается и тревожется",
    "Многосторонний человек, открыт новому опыту",
    "В общении с людьми старается не проявлять истинные эмоции",
    "Можно сказать, что это сочувствующий и добросердечный человек",
    "Действия скорее спонтанные, чем последовательные",
    "Относит себя к эмоционально стабильным и спокойным людям",
    "Можно сказать, что это консервативный человек, тяжело принимающий новое"
]

N_QUESTIONS = len(SURVEY_QUESTIONS)


class SurveyStates(StatesGroup):
    QUESTION = State()
    END = State()


class PartnerSurveyStates(StatesGroup):
    QUESTION = State()
    END = State()


class SurveyQuestionChoice(Enum):
    MINUS_TWO = "-2"
    MINUS_ONE = "-1"
    ZERO = "0"
    PLUS_ONE = "1"
    PLUS_TWO = "2"

    @classmethod
    def has_value(cls, value):
        """
        Checks if the provided value is a valid program name.
        """
        return value in cls._value2member_map_


survey_keyboard = create_reply_keyboard(SurveyQuestionChoice, buttons_per_row=5)


async def check_valid_answer(message: types.Message):
    answer: str = message.text
    if not SurveyQuestionChoice.has_value(answer):
        await send_msg_user(message.from_user.id, 
                            "Выбери ответ из представленных",
                            reply_markup=survey_keyboard,
                            fail=True)
        return False
    return True


@router.message(StateFilter(None), Command("survey"))
@checker
@check_finished_profile
async def cmd_survey(message: types.Message, state: FSMContext):
    await send_msg_user(message.from_user.id, 
                        f"Нужно будет ответить на {N_QUESTIONS} утверждений о себе\n\n\"-2\" - совсем не я\n\"2\" - буквально я")

    await send_msg_user(message.from_user.id, 
                        f"[Шаг 1/{N_QUESTIONS}]\n{SURVEY_QUESTIONS[0]}", 
                        reply_markup=survey_keyboard)

    await state.set_state(SurveyStates.QUESTION)
    await state.update_data(number=1)


@router.message(StateFilter(SurveyStates.QUESTION))
@checker
@contains_command
async def survey_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    number = int(data.get("number"))

    if not check_valid_answer(message):
        return

    answer: str = message.text

    await update_user(message.from_user.id, 
                      {f"survey.question{number}": answer})

    await state.update_data(number=number + 1)
    next_question = SURVEY_QUESTIONS[number]

    await send_msg_user(message.from_user.id, 
                        f"[Шаг {number + 1}/{N_QUESTIONS}]\n{next_question}", 
                        reply_markup=survey_keyboard)

    if number < N_QUESTIONS - 1:
        await state.set_state(SurveyStates.QUESTION)
    else:
        await state.set_state(SurveyStates.END)


@router.message(StateFilter(SurveyStates.END))
@checker
@contains_command
async def survey_end(message: types.Message, state: FSMContext):
    if not check_valid_answer(message):
        return

    answer: str = message.text


    await update_user(message.from_user.id, 
                      {f"survey.question10": answer,
                       "survey.finished": "yes"})

    await send_msg_user(message.from_user.id, 
                        "Отлично, ты всегда можешь пройти опрос заново через /survey",
                        reply_markup=types.ReplyKeyboardRemove())

    await send_msg_user(message.from_user.id, 
                        "Теперь, пожалуйста, ответь на те же утверждения, только относительно своего партнера через /partner_survey")
    await state.clear()


@router.message(StateFilter(None), Command("partner_survey"))
@checker
@check_finished_profile
async def cmd_partner_survey(message: types.Message, state: FSMContext):
    await send_msg_user(message.from_user.id, 
                        f"Теперь нужно будет ответить на {N_QUESTIONS} утверждений о потенциальном партнере")

    await send_msg_user(message.from_user.id, 
                        f"[Шаг 1/{N_QUESTIONS}]\n{PARTNER_SURVEY_QUESTIONS[0]}", 
                        reply_markup=survey_keyboard)

    await state.set_state(PartnerSurveyStates.QUESTION)
    await state.update_data(number=1)


@router.message(StateFilter(PartnerSurveyStates.QUESTION))
@checker
@contains_command
async def partner_survey_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    number = int(data.get("number"))

    if not check_valid_answer(message):
        return

    answer: str = message.text


    await update_user(message.from_user.id, 
                      {f"partner_survey.question{number}": answer})

    await state.update_data(number=number + 1)
    next_question = PARTNER_SURVEY_QUESTIONS[number]

    await send_msg_user(message.from_user.id, 
                        f"[Шаг {number + 1}/{N_QUESTIONS}]\n{next_question}", 
                        reply_markup=survey_keyboard)

    if number < N_QUESTIONS - 1:
        await state.set_state(PartnerSurveyStates.QUESTION)
    else:
        await state.set_state(PartnerSurveyStates.END)


@router.message(StateFilter(PartnerSurveyStates.END))
@checker
@contains_command
async def partner_survey_question(message: types.Message, state: FSMContext):
    if not check_valid_answer(message):
        return

    answer: str = message.text

    await update_user(message.from_user.id,
                        {f"partner_survey.question10": answer,
                         "partner_survey.finished": "yes"})

    await send_msg_user(message.from_user.id, 
                        "Отлично, ты всегда можешь пройти этот опрос заново через /partner_survey",
                        reply_markup=types.ReplyKeyboardRemove())

    await send_msg_user(message.from_user.id, 
                        "На этом все!\nОсталось дождаться результатов мэтчинга\n\nP.S. ты можешь добавить человека в свой /blacklist")
    await state.clear()