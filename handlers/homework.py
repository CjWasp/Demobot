from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

import database as db
from course_content import DEMO_LESSONS
from keyboards import main_menu_keyboard
from config import ADMIN_IDS

router = Router()


def get_lesson(lesson_id: int):
    return next((l for l in DEMO_LESSONS if l["id"] == lesson_id), None)


class HomeworkStates(StatesGroup):
    waiting_for_answer = State()


@router.callback_query(F.data.startswith("hw_start:"))
async def hw_from_lesson(callback: CallbackQuery, state: FSMContext):
    lesson_id = int(callback.data.split(":")[1])
    lesson = get_lesson(lesson_id)
    if not lesson:
        await callback.answer("Урок не найден.", show_alert=True)
        return

    await state.update_data(lesson_id=lesson_id)
    await callback.message.answer(
        "<i>Напишите ваш ответ и отправьте как обычное сообщение</i>",
        parse_mode="HTML"
    )
    await state.set_state(HomeworkStates.waiting_for_answer)
    await callback.answer()


@router.message(HomeworkStates.waiting_for_answer)
async def receive_homework(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lesson_id = data["lesson_id"]
    user = db.get_user(message.from_user.id)
    lesson = get_lesson(lesson_id)

    answer_text = message.caption or message.text or "[файл без подписи]"
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id

    await state.clear()
    await message.answer(
        "✅ <b>Задание отправлено!</b>\n\n"
        "Нажмите «📚 Уроки» чтобы продолжить.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

    lesson_title = lesson["title"] if lesson else f"Урок {lesson_id}"
    notify_text = (
        f"📬 <b>Задание (демо)</b>\n"
        f"👤 {user['full_name']} (@{user.get('username') or '—'})\n"
        f"📖 {lesson_title}\n\n"
        f"💬 {answer_text[:500]}"
    )
    for admin_id in ADMIN_IDS:
        try:
            if file_id:
                await bot.send_photo(admin_id, file_id, caption=notify_text, parse_mode="HTML")
            else:
                await bot.send_message(admin_id, notify_text, parse_mode="HTML")
        except Exception:
            pass
