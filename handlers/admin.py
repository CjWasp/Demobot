from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database as db
from keyboards import admin_keyboard, main_menu_keyboard
from config import ADMIN_IDS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class BroadcastState(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirm = State()


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет доступа.")
        return
    stats = db.get_stats()
    await message.answer(
        f"🔧 <b>Демо — Панель администратора</b>\n\n"
        f"👥 Пользователей: {stats['total']}\n"
        f"🏁 Завершили демо: {stats['done']}",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📈 Статистика")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    stats = db.get_stats()
    await message.answer(
        f"📈 <b>Статистика демо</b>\n\n"
        f"👥 Всего: <b>{stats['total']}</b>\n"
        f"🏁 Завершили: <b>{stats['done']}</b>",
        parse_mode="HTML"
    )


@router.message(F.text == "👥 Студенты")
async def show_students(message: Message):
    if not is_admin(message.from_user.id):
        return
    users = db.get_all_users()
    if not users:
        await message.answer("Студентов пока нет.")
        return

    await message.answer(f"👥 <b>Все студенты ({len(users)}):</b>", parse_mode="HTML")
    for user in users:
        status = "🏁 завершил" if user["demo_done"] else f"📖 урок {user['current_lesson']}"
        username = f"@{user['username']}" if user["username"] else "—"
        text = (
            f"👤 <b>{user['full_name']}</b>\n"
            f"🔗 {username}\n"
            f"📊 {status}\n"
            f"🆔 {user['user_id']}"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="🗑 Удалить", callback_data=f"delete_user:{user['user_id']}")
        await message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("delete_user:"))
async def delete_user_ask(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    user_id = int(callback.data.split(":")[1])
    user = db.get_user(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, удалить", callback_data=f"delete_user_confirm:{user_id}")
    builder.button(text="❌ Отмена", callback_data="delete_user_cancel")
    builder.adjust(2)
    await callback.message.edit_text(
        f"🗑 Удалить студента <b>{user['full_name']}</b>?",
        parse_mode="HTML", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_user_confirm:"))
async def delete_user_confirm(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    user_id = int(callback.data.split(":")[1])
    user = db.get_user(user_id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return
    name = user["full_name"]
    db.delete_user(user_id)
    await callback.message.edit_text(f"🗑 Студент <b>{name}</b> удалён.", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "delete_user_cancel")
async def delete_user_cancel(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Отменено.")


@router.message(F.text == "📢 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "Напишите сообщение для рассылки.\n\n"
        "<i>Используйте {имя} чтобы вставить имя студента</i>",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastState.waiting_for_message)


@router.message(BroadcastState.waiting_for_message)
async def broadcast_preview(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    text = message.text
    users = db.get_all_users()
    count = len(users)
    await state.update_data(text=text)

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, отправить", callback_data="broadcast_confirm")
    builder.button(text="❌ Отмена", callback_data="broadcast_cancel")
    builder.adjust(2)

    await message.answer(
        f"📢 <b>Предпросмотр:</b>\n\n{text}\n\n"
        f"─────────────────\n"
        f"Получателей: <b>{count}</b>\n"
        f"<i>💡 {{имя}} будет заменено на имя каждого студента</i>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await state.set_state(BroadcastState.waiting_for_confirm)


@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_send(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    data = await state.get_data()
    text = data.get("text", "")
    await state.clear()

    users = db.get_all_users()
    sent, failed = 0, 0
    for user in users:
        try:
            personalized = text.replace("{имя}", user["full_name"].split()[0])
            await bot.send_message(
                user["user_id"],
                f"📢 <b>Сообщение от куратора:</b>\n\n{personalized}",
                parse_mode="HTML"
            )
            sent += 1
        except Exception:
            failed += 1

    await callback.message.edit_text(
        f"✅ Рассылка завершена!\n\nОтправлено: {sent}\nОшибок: {failed}"
    )
    await callback.answer()


@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Рассылка отменена.")


@router.message(F.text == "🔙 Выйти из админки")
async def exit_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Вышли из админки.", reply_markup=main_menu_keyboard())
