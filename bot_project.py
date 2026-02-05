import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# --- Настройки ---
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    exit("Ошибка: Токен не найден! Проверьте файл .env")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Имитация базы данных
registered_users = set() 
user_reviews = {} 

class ReviewState(StatesGroup):
    waiting_for_text = State()

# --- КЛАВИАТУРЫ (Объявляем в начале) ---

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="📊 Статистика", callback_data="stats"))
    builder.row(types.InlineKeyboardButton(text="📝 Регистрация", callback_data="register_me"))
    builder.row(types.InlineKeyboardButton(text="❓ Вопросы", callback_data="faq"))
    builder.row(types.InlineKeyboardButton(text="👨‍🏫 Преподаватели", callback_data="teachers"))
    builder.row(types.InlineKeyboardButton(text="💬 Отзывы", callback_data="reviews_menu"))
    builder.row(types.InlineKeyboardButton(text="ℹ️ О нас", callback_data="about"))
    return builder.as_markup()

def faq_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Какие документы необходимы для поступления?", 
        callback_data="faq_docs_detail")
    )
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_main"))
    return builder.as_markup()

def stars_keyboard():
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(types.InlineKeyboardButton(text=f"{i} ⭐", callback_data=f"star_{i}"))
    return builder.as_markup()

# --- ХЕНДЛЕРЫ ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Добро пожаловать в бот Техникума! Выберите раздел:", reply_markup=main_menu())

@dp.callback_query(F.data == "register_me")
async def register_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in registered_users:
        await callback.answer("Вы уже зарегистрированы! ✅", show_alert=True)
    else:
        registered_users.add(user_id)
        await callback.answer("Регистрация прошла успешно! 🎉", show_alert=True)
        await callback.message.edit_text("Регистрация завершена! Теперь вам доступна статистика.", reply_markup=main_menu())

@dp.callback_query(F.data == "faq")
async def faq_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("❓ Выберите интересующий вас вопрос:", reply_markup=faq_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "faq_docs_detail")
async def faq_docs_detail_handler(callback: types.CallbackQuery):
    text = (
        "<b>Документы для подачи заявления:</b>\n"
        "Заявление\nАттестат или диплом\nКопия паспорта\nФото 3*4 4 шт.\n\n"
        "<b>Документы для зачисления:</b>\n"
        "Заявление\nАттестат или диплом\nКопия паспорта\nФото 3*4 4 шт.\n"
        "Копия ИНН\nКопия СНИЛС\nКопия Полиса ОМС"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 К вопросам", callback_data="faq"))
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите раздел:", reply_markup=main_menu())
    await callback.answer()

@dp.callback_query(F.data == "reviews_menu")
async def reviews_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_reviews:
        await callback.message.edit_text(f"Ваш отзыв: {user_reviews[user_id]}", reply_markup=main_menu())
    else:
        await callback.message.edit_text("Выберите сколько звезд поставите:", reply_markup=stars_keyboard())
    await callback.answer()

@dp.callback_query(F.data.startswith("star_"))
async def star_select(callback: types.CallbackQuery, state: FSMContext):
    stars = callback.data.split("_")[1]
    await state.update_data(stars=stars)
    await callback.message.answer(f"Вы выбрали {stars} ⭐. Теперь напишите текст отзыва:")
    await state.set_state(ReviewState.waiting_for_text)
    await callback.answer()

@dp.message(ReviewState.waiting_for_text)
async def process_review_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    stars = data.get("stars")
    user_reviews[message.from_user.id] = f"{stars}/5: {message.text}"
    await message.answer("✅ Отзыв принят!", reply_markup=main_menu())
    await state.clear()

@dp.callback_query(F.data == "teachers")
async def teachers_handler(callback: types.CallbackQuery):
    text = (
        "<b>👨‍🏫 Наши преподаватели:</b>\n\n"
        "• Новикова Елизавета Александровна — Преподаватель Математики\n"
        "• Федотов Мирон Ильич — Преподаватель Истории\n"
        "• Цветков Никита Всеволодович — Преподаватель Информатики\n"
        "• Макаров Али Тимофеевич — Преподаватель Географии\n"
        "• Семенова Алиса Сергеевна — Преподаватель Физкультуры\n"
        "• Ларионов Михаил Данилович — Преподаватель Русского языка\n"
        "• Андреев Арсений Иванович — Преподаватель ОБЖ"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main"))
    
    try:
        await callback.message.edit_text(
            text, 
            reply_markup=builder.as_markup(), 
            parse_mode="HTML"
        )
    except TelegramBadRequest:
        await callback.answer()
    await callback.answer()

@dp.callback_query(F.data == "about")
async def about_handler(callback: types.CallbackQuery):
    text = (
        "<b>📜 О нашем техникуме</b>\n\n"
        "У техникума богатейшая история, а начиналась она в далеком 1930 году в городе Сарапуле, "
        "на берегу красавицы-реки Камы.\n\n"
        "В то время набирала темпы культурная революция, страна задыхалась от безграмотности, "
        "нуждалась в квалифицированных кадрах не только для подъема промышленности, но и для села.\n\n"
        "Поэтому, в соответствии с постановлением Уральского областного союза потребкооперации "
        "1 сентября 1930 года, в Сарапуле был открыт <b>Сарапульский кооперативный техникум</b>."
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main"))
    
    try:
        await callback.message.edit_text(
            text, 
            reply_markup=builder.as_markup(), 
            parse_mode="HTML"
        )
    except Exception:
        await callback.answer()
    await callback.answer()

@dp.callback_query(F.data == "stats")
async def stats_handler(callback: types.CallbackQuery):
    # Проверка регистрации
    if callback.from_user.id not in registered_users:
        await callback.answer("⚠️ Ошибка! Сначала пройдите регистрацию.", show_alert=True)
        return

    # Текст статистики
    text = (
        "<b>📊 Статистика успеваемости групп:</b>\n\n"
        "📈 ИСП 23 — 101% (Лидеры!)\n"
        "📈 ИСП 34 — 97%\n"
        "📈 ИСП 41 — 95%\n"
        "📈 ИСП 21 — 94%\n"
        "📈 ИСП 12 — 91%\n\n"
        "<i>Данные обновлены на текущий момент.</i>"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main"))
    
    try:
        await callback.message.edit_text(
            text, 
            reply_markup=builder.as_markup(), 
            parse_mode="HTML"
        )
    except Exception:
        # Если текст уже выведен, просто убираем "часики" на кнопке
        await callback.answer()
    await callback.answer()

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())