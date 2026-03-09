import asyncio
import math
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardButton, InlineKeyboardMarkup

# --- НАСТРОЙКИ (ОБЯЗАТЕЛЬНО ЗАПОЛНИ) ---
TOKEN = "8645411569:AAHLKUzl-d0OIQWXNuIPamkLeXo2tO7mFho"
ADMIN_ID = 1081724056  # Твой цифровой ID
ADMIN_USERNAME = "@NakrutsBot_admin"
VIP_USERS = ["ThxGoodd", "NakrutsBot_admin"] # Юзернеймы без @

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временная база данных в оперативной памяти
users_db = {}

class OrderState(StatesGroup):
    choosing_platform = State()
    entering_amount = State()
    entering_link = State()

# --- КЛАВИАТУРЫ ---
def main_menu():
    kb = [
        [types.KeyboardButton(text="🚀 Накрутка Telegram"), types.KeyboardButton(text="📸 Накрутка Instagram")],
        [types.KeyboardButton(text="🎁 Тест (Бесплатно)"), types.KeyboardButton(text="👤 Профиль")],
        [types.KeyboardButton(text="💳 Оплата картой")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def back_kb():
    return types.ReplyKeyboardMarkup(keyboard=[[types.KeyboardButton(text="⬅️ Назад")]], resize_keyboard=True)

# --- ПРИВЕТСТВИЕ И СТАРТ ---
@dp.message(Command("start"))
async def start(message: types.Message):
    u_id = message.from_user.id
    username = message.from_user.username
    
    if u_id not in users_db:
        users_db[u_id] = {
            'test_used': False, 
            'total_orders': 0, 
            'total_subs': 0, 
            'reg_date': datetime.now().strftime("%d.%m.%Y")
        }
    
    welcome_text = (
        "Здравствуйте это **NAKRUTS_BOT**✔️\n\n"
        "С помощью этого бота вы можете накрутить себе подписчиков в Телеграм канале либо в Инстаграм аккаунте✔️\n\n"
        "Другие предложения как TikTok, VK и т.д. пока что в разработке🔄"
    )
    
    if username in VIP_USERS:
        welcome_text += "\n\n⭐ **Статус:** VIP Администратор"

    await message.answer(welcome_text, reply_markup=main_menu())

# --- КНОПКА НАЗАД ---
@dp.message(F.text == "⬅️ Назад")
async def go_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Возвращаюсь в главное меню", reply_markup=main_menu())

# --- ПРОФИЛЬ ---
@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):
    # Пытаемся достать данные, если их нет - ставим заглушки, чтобы бот не падал
    user_id = message.from_user.id
    u = users_db.get(user_id, {
        'reg_date': '10.03.2026',
        'total_orders': 0,
        'total_subs': 0
    })
    
    text = (f"👤 **Профиль пользователя**\n\n"
            f"🆔 Ваш TG ID: `{user_id}`\n"
            f"📅 Дата регистрации: {u['reg_date']}\n"
            f"📦 Всего заказов: {u['total_orders']}\n"
            f"📈 Накручено всего: {u['total_subs']} подп.")
    
    await message.answer(text, parse_mode="Markdown")

# --- ОПЛАТА КАРТОЙ ---
@dp.message(F.text == "💳 Оплата картой")
async def pay_card(message: types.Message):
    msg_to_admin = "Привет я хочу накрутить подписчеков Хочу сделать оплату с картой."
    link = f"https://t.me/{ADMIN_USERNAME[1:]}?text={msg_to_admin.replace(' ', '%20')}"
    
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Написать Админу", url=link)]
    ])
    await message.answer(
        f"Оплата картой происходит через Админа.\n\n"
        f"Пожалуйста, напишите админу для оплаты картой:\n"
        f"Админ >>> {ADMIN_USERNAME}", 
        reply_markup=inline_kb
    )

# --- ТЕСТОВАЯ НАКРУТКА ---
@dp.message(F.text == "🎁 Тест (Бесплатно)")
async def test_drive(message: types.Message):
    u = users_db.get(message.from_user.id)
    if u['test_used'] and message.from_user.id != ADMIN_ID:
        await message.answer("❌ Кнопку тест можно использовать только один раз!")
        return
    
    kb = [
        [types.KeyboardButton(text="🤖 TG Тест"), types.KeyboardButton(text="📸 Inst Тест")],
        [types.KeyboardButton(text="⬅️ Назад")]
    ]
    await message.answer("🎁 Тестовая накрутка: 10 подписчиков бесплатно.\nВыберите платформу:", 
                         reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(F.text.in_(["🤖 TG Тест", "📸 Inst Тест"]))
async def test_step_2(message: types.Message, state: FSMContext):
    platform = "Telegram" if "TG" in message.text else "Instagram"
    await state.update_data(platform=platform, is_test=True, amount=10)
    await message.answer(f"Пришлите ссылку на ваш {platform}:", reply_markup=back_kb())
    await state.set_state(OrderState.entering_link)

# --- ОСНОВНАЯ НАКРУТКА ---
@dp.message(F.text.in_(["🚀 Накрутка Telegram", "📸 Накрутка Instagram"]))
async def start_order(message: types.Message, state: FSMContext):
    platform = "TG" if "Telegram" in message.text else "INST"
    limit_text = "Минимально: 250\nМаксимально: 20000" if platform == "TG" else "Минимально: 250\nМаксимально: 60000"
    
    await state.update_data(platform=platform, is_test=False)
    await message.answer(f"Введите количество подписчиков.\n\n{limit_text}\nЦена: 0.1 ⭐ за 1 подп.", reply_markup=back_kb())
    await state.set_state(OrderState.entering_amount)

@dp.message(OrderState.entering_amount)
async def process_amount(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Число должно состоять только из цифр!")
        return
    
    amount = int(message.text)
    data = await state.get_data()
    platform = data['platform']
    
    min_q = 250
    max_q = 20000 if platform == "TG" else 60000
    
    if amount < min_q or amount > max_q:
        await message.answer(f"Ошибка! Количество должно быть от {min_q} до {max_q}")
        return
    
    # Расчет цены с округлением вверх
    raw_price = amount * 0.1
    price = math.ceil(raw_price)
    
    await state.update_data(amount=amount, price=price)
    await message.answer(f"Сумма к оплате: {price} ⭐\nПришлите ссылку на канал/аккаунт:")
    await state.set_state(OrderState.entering_link)

@dp.message(OrderState.entering_link)
async def process_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    u_id = message.from_user.id
    
    if data.get('is_test'):
        users_db[u_id]['test_used'] = True
        await message.answer("✅ Тестовый заказ принят! Время накрутки 10 подписчиков: ~15-30 минут.", reply_markup=main_menu())
        await state.clear()
    else:
        # Если юзер VIP - пропускаем оплату
        if message.from_user.username in VIP_USERS:
            await message.answer(f"🔥 VIP-заказ на {data['amount']} подп. принят бесплатно!", reply_markup=main_menu())
            await state.clear()
            return

        await message.answer_invoice(
            title=f"Накрутка {data['platform']}",
            description=f"Заказ: {data['amount']} подп. на {message.text}",
            payload=f"order_{u_id}",
            provider_token="", 
            currency="XTR",
            prices=[LabeledPrice(label="Оплата", amount=data['price'])]
        )

@dp.pre_checkout_query()
async def checkout_confirm(query: PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def payment_done(message: types.Message):
    u_id = message.from_user.id
    users_db[u_id]['total_orders'] += 1
    await message.answer("🔥 Оплата прошла! Накрутка запущена.", reply_markup=main_menu())

async def main():
    print("🚀 Бот NAKRUTS запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())

