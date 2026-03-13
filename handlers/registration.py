from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove

import database as db
from keyboards import main_menu_keyboard

router = Router()


class RegState(StatesGroup):
    waiting_for_name = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    if user:
        await message.answer(
            f"С возвращением, <b>{user['full_name'].split()[0]}</b>! 👋\n\n"
            "Нажми «📚 Уроки» чтобы продолжить.",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
        return

    await message.answer(
        "Давайте знакомиться. Как вас зовут?",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await state.set_state(RegState.waiting_for_name)


@router.message(RegState.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    if len(full_name) < 2:
        await message.answer("Пожалуйста, введите имя.")
        return

    db.create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=full_name
    )
    await state.clear()
    await message.answer(
        f"Отлично, <b>{full_name.split()[0]}</b>! 🎉\n\n"
        "Добро пожаловать в демо-версию курса по финансовой грамотности.\n\n"
        "Нажми «📚 Уроки» чтобы начать 👇",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
