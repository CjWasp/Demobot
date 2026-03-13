from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from course_content import DEMO_LESSONS, TOTAL_DEMO_LESSONS, DEMO_FINAL_MESSAGE
from keyboards import main_menu_keyboard

router = Router()


def get_lesson(lesson_id: int):
    return next((l for l in DEMO_LESSONS if l["id"] == lesson_id), None)


def lesson_keyboard_before_start(lesson: dict):
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Начать", callback_data=f"watch_lesson:{lesson['id']}")
    builder.adjust(1)
    return builder.as_markup()


def lesson_keyboard_after_start(lesson: dict):
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️ Смотреть урок", url=lesson["video_url"])
    if lesson["extra_video_url"]:
        builder.button(text=f"🔗 {lesson['extra_video_label']}", url=lesson["extra_video_url"])
    if lesson["hw_type"] == "text":
        builder.button(text="✏️ Выполнить задание", callback_data=f"hw_start:{lesson['id']}")
    builder.button(text="✅ Завершить урок", callback_data=f"mark_done:{lesson['id']}")
    builder.adjust(1)
    return builder.as_markup()


def lessons_list_keyboard(current_lesson_id: int):
    builder = InlineKeyboardBuilder()
    for lesson in DEMO_LESSONS:
        lid = lesson["id"]
        if lid < current_lesson_id:
            label = f"✅ {lesson['title']}"
        elif lid == current_lesson_id:
            label = f"▶️ {lesson['title']}"
        else:
            label = f"🔒 {lesson['title']}"
        cb = f"open_lesson:{lid}" if lid <= current_lesson_id else "locked"
        builder.button(text=label, callback_data=cb)
    builder.adjust(1)
    return builder.as_markup()


async def send_lesson(target, lesson: dict):
    hw_block = f"\n\n{lesson['hw_text']}" if lesson.get("hw_text") else ""
    caption = f"{lesson['text']}{hw_block}"
    keyboard = lesson_keyboard_before_start(lesson)

    if lesson.get("cover"):
        await target.answer_photo(
            photo=lesson["cover"], caption=caption,
            reply_markup=keyboard, parse_mode="HTML"
        )
    else:
        await target.answer(caption, reply_markup=keyboard, parse_mode="HTML",
                            disable_web_page_preview=True)


@router.message(F.text == "📚 Уроки")
async def show_lessons(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Нажми /start чтобы начать.")
        return

    if user["demo_done"]:
        await message.answer(
            "🎉 Ты уже прошёл всё демо!\n\n"
            "Чтобы продолжить обучение, напиши куратору: @sergofinance",
            reply_markup=main_menu_keyboard()
        )
        return

    cur = user["current_lesson"]
    done = cur - 1
    await message.answer(
        f"📚 <b>Демо-курс</b>\n\nПройдено: <b>{done}</b> из {TOTAL_DEMO_LESSONS} уроков",
        reply_markup=lessons_list_keyboard(cur),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "locked")
async def locked(callback: CallbackQuery):
    await callback.answer("🔒 Сначала завершите текущий урок!", show_alert=True)


@router.callback_query(F.data.startswith("open_lesson:"))
async def open_lesson(callback: CallbackQuery):
    lesson_id = int(callback.data.split(":")[1])
    user = db.get_user(callback.from_user.id)
    if not user or lesson_id > user["current_lesson"]:
        await callback.answer("🔒 Урок ещё не открыт!", show_alert=True)
        return
    lesson = get_lesson(lesson_id)
    if not lesson:
        await callback.answer("Урок не найден.", show_alert=True)
        return
    # Убираем клавиатуру со списком уроков перед отправкой урока
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await send_lesson(callback.message, lesson)
    await callback.answer()


@router.callback_query(F.data.startswith("watch_lesson:"))
async def watch_lesson(callback: CallbackQuery):
    lesson_id = int(callback.data.split(":")[1])
    lesson = get_lesson(lesson_id)
    if not lesson:
        await callback.answer()
        return
    try:
        await callback.message.edit_reply_markup(
            reply_markup=lesson_keyboard_after_start(lesson)
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("mark_done:"))
async def mark_done(callback: CallbackQuery, bot: Bot):
    lesson_id = int(callback.data.split(":")[1])
    user = db.get_user(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка. Напишите /start", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)

    if lesson_id == user["current_lesson"]:
        if lesson_id >= TOTAL_DEMO_LESSONS:
            db.complete_demo(callback.from_user.id)
            await callback.message.answer(
                DEMO_FINAL_MESSAGE,
                parse_mode="HTML",
                reply_markup=main_menu_keyboard()
            )
        else:
            db.advance_lesson(callback.from_user.id)
            next_lesson = get_lesson(lesson_id + 1)
            await send_lesson(callback.message, next_lesson)

    await callback.answer()


@router.callback_query(F.data.startswith("hw_start:"))
async def hw_start(callback: CallbackQuery):
    from aiogram.fsm.context import FSMContext
    await callback.answer("Просто напишите ваш ответ как обычное сообщение 👇")


@router.message(F.text == "📊 Прогресс")
async def show_progress(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Нажми /start чтобы начать.")
        return

    cur = user["current_lesson"]
    done = cur - 1 if not user["demo_done"] else TOTAL_DEMO_LESSONS
    pct = round(done / TOTAL_DEMO_LESSONS * 100)
    bar_filled = int(pct / 10)
    bar = "🟩" * bar_filled + "⬜" * (10 - bar_filled)

    status = "✅ Демо завершено!" if user["demo_done"] else f"Урок {cur} из {TOTAL_DEMO_LESSONS}"

    await message.answer(
        f"📊 <b>Прогресс</b>\n\n"
        f"👤 {user['full_name']}\n"
        f"📖 {status}\n\n"
        f"{bar} {pct}%",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
