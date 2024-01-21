import asyncio
import json
import logging
import os
from dotenv import load_dotenv
from aiogram.types.input_file import FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot, Dispatcher, F
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove, ChatJoinRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, StateFilter
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated


load_dotenv()
owner_id = 713690896
API_TOKEN = os.getenv('TOKEN')
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

available_vehicle_names = ["Автомобиль", "Поезд", "Самолет"]


def make_row_keyboard(items: list[str]):
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)


class RegistrationStates(StatesGroup):
    VEHICLE = State()
    NAME = State()
    PHONE = State()
    EMAIL = State()
    DEPARTURE_CITY = State()
    ARRIVAL_CITY = State()
    WEIGHT = State()
    AVAILABLE_WEIGHT = State()
    DEPARTURE_MONTH = State()
    DEPARTURE_DATE = State()
    ARRIVAL_MONTH = State()
    ARRIVAL_DATE = State()


@dp.message(StateFilter(None), Command("add_route"))
async def cmd_vehicle(msg: Message, state: FSMContext):
    await msg.answer(text="Выберите ТС:", reply_markup=make_row_keyboard(available_vehicle_names))
    await state.set_state(RegistrationStates.VEHICLE)


@dp.message(RegistrationStates.VEHICLE)
async def vehicle_chosen(msg: Message, state: FSMContext):
    await state.update_data(name_vehicle=msg.text)

    user_data = await state.get_data()
    name_vehicle = user_data.get('name_vehicle', '')
    if name_vehicle == 'Самолет':
        name_vehicle = 1
    elif name_vehicle == 'Поезд':
        name_vehicle = 2
    else:
        name_vehicle = 3
    await state.update_data(name_vehicle=name_vehicle)

    await msg.answer("Введите ваше имя:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RegistrationStates.NAME)


@dp.message(RegistrationStates.NAME)
async def process_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("Введите ваш телефон:")
    await state.set_state(RegistrationStates.PHONE)


@dp.message(RegistrationStates.PHONE)
async def process_phone(msg: Message, state: FSMContext):
    await state.update_data(phone=msg.text)
    await msg.answer("Введите вашу почту:")
    await state.set_state(RegistrationStates.EMAIL)


@dp.message(RegistrationStates.EMAIL)
async def process_email(msg: Message, state: FSMContext):
    await state.update_data(email=msg.text)
    await msg.answer("Введите город отправления:")
    await state.set_state(RegistrationStates.DEPARTURE_CITY)


@dp.message(RegistrationStates.DEPARTURE_CITY)
async def process_departure_city(msg: Message, state: FSMContext):
    await state.update_data(departure_city=msg.text)
    await msg.answer("Введите город прибытия:")
    await state.set_state(RegistrationStates.ARRIVAL_CITY)


@dp.message(RegistrationStates.ARRIVAL_CITY)
async def process_arrival_city(msg: Message, state: FSMContext):
    await state.update_data(arrival_city=msg.text)
    await msg.answer("Введите вес вашего багажа:")
    await state.set_state(RegistrationStates.WEIGHT)


@dp.message(RegistrationStates.WEIGHT)
async def process_arrival_city(msg: Message, state: FSMContext):
    await state.update_data(baggage_weight=msg.text)
    await msg.answer("Сколько кг готовы взять?")
    await state.set_state(RegistrationStates.AVAILABLE_WEIGHT)


@dp.message(RegistrationStates.AVAILABLE_WEIGHT)
async def process_weight(msg: Message, state: FSMContext):
    await state.update_data(available_baggage_space=msg.text)
    builder = InlineKeyboardBuilder()
    builder.add(*[InlineKeyboardButton(text=str(month), callback_data=f"month_{month}") for month in range(1, 13)])
    builder.adjust(4)
    await msg.answer("Укажите месяц отправления:", reply_markup=builder.as_markup())
    await state.set_state(RegistrationStates.DEPARTURE_MONTH)


@dp.callback_query(RegistrationStates.DEPARTURE_MONTH)
async def process_departure_month(callback: CallbackQuery, state: FSMContext):
    await state.update_data(departure_month=callback.data.split("_")[1])
    calendar = InlineKeyboardBuilder()
    calendar.adjust(1)
    calendar.add(*[InlineKeyboardButton(text=str(day), callback_data=f"date_{day}") for day in range(1, 32)])
    await callback.message.answer("Выберите дату отправления:", reply_markup=calendar.as_markup())
    await state.set_state(RegistrationStates.DEPARTURE_DATE)


@dp.callback_query(RegistrationStates.DEPARTURE_DATE)
async def process_departure_date(callback: CallbackQuery, state: FSMContext):
    await state.update_data(departure_date=callback.data.split("_")[1])

    user_data = await state.get_data()
    departure_month = user_data.get('departure_month', '')
    departure_day = user_data.get('departure_date', '')

    month_prefix = '' if int(departure_month) >= 10 else '0'
    day_prefix = '' if int(departure_day) >= 10 else '0'

    departure_date = f"{'2024'}-{month_prefix}{departure_month}-{day_prefix}{departure_day}"
    await state.update_data(departure_date=departure_date)

    builder = InlineKeyboardBuilder()
    builder.add(*[InlineKeyboardButton(text=str(month), callback_data=f"month_{month}") for month in range(1, 13)])
    builder.adjust(4)
    await callback.message.answer("Укажите месяц прибытия:", reply_markup=builder.as_markup())
    await state.set_state(RegistrationStates.ARRIVAL_MONTH)


@dp.callback_query(RegistrationStates.ARRIVAL_MONTH)
async def process_arrival_month(callback: CallbackQuery, state: FSMContext):
    await state.update_data(arrival_month=callback.data.split("_")[1])
    calendar = InlineKeyboardBuilder()
    calendar.adjust(1)
    calendar.add(*[InlineKeyboardButton(text=str(day), callback_data=f"date_{day}") for day in range(1, 32)])
    await callback.message.answer("Выберите дату прибытия:", reply_markup=calendar.as_markup())
    await state.set_state(RegistrationStates.ARRIVAL_DATE)


@dp.callback_query(RegistrationStates.ARRIVAL_DATE)
async def process_arrival_date(callback: CallbackQuery, state: FSMContext):
    await state.update_data(arrival_date=callback.data.split("_")[1])

    user_data = await state.get_data()
    arrival_month = user_data.get('arrival_month', '')
    arrival_day = user_data.get('arrival_date', '')

    month_prefix = '' if int(arrival_month) >= 10 else '0'
    day_prefix = '' if int(arrival_day) >= 10 else '0'

    arrival_date = f"{'2024'}-{month_prefix}{arrival_month}-{day_prefix}{arrival_day}"
    await state.update_data(arrival_date=arrival_date)

    await callback.message.answer("Спасибо за заполнение!")

    user_data = await state.get_data()
    del user_data['departure_month']
    del user_data['arrival_month']

    result_json = {
        "name_vehicle": user_data.get('name_vehicle', ''),
        "name": user_data.get('name', ''),
        "phone": user_data.get('phone', ''),
        "email": user_data.get('email', ''),
        "departure_date": user_data.get('departure_date', ''),
        "departure_city": user_data.get('departure_city', ''),
        "arrival_date": user_data.get('arrival_date', ''),
        "arrival_city": user_data.get('arrival_city', ''),
        "baggage_weight": user_data.get('baggage_weight', ''),
        "available_baggage_space": user_data.get('available_baggage_space', '')
    }

    user_json = json.dumps(result_json, ensure_ascii=False, indent=4)

    await callback.message.answer(
        f"Ваши данные сохранены:\n\n {user_json}"
    )

    # Записываем данные пользователя в файл
    file_path = "user_data.json"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(user_json)

    # Отправляем файл только владельцу бота
    document = FSInputFile(file_path)
    await bot.send_document(owner_id, document)

    await state.clear()


@dp.message(F.new_chat_members)
async def new_member(msg: Message):
    if msg.from_user.last_name is not None:
        await bot.send_message(
            msg.chat.id, f'Привет, {msg.from_user.first_name} {msg.from_user.last_name}! 👋\n'
            "Добро пожаловать на Ticketbag – Ваш партнер в каждом путешествии!\n\n"
            "На TicketBag Вы найдете партнеров для перевозки багажа, "
            "и сможете предложить свободное место в вашем багаже другим пользователям.\n\n"
            "Чтобы добавить маршрут используй @Ticketbag_bot\n",
            parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )
    else:
        await bot.send_message(
            msg.chat.id, f'Привет, {msg.from_user.first_name}! 👋\n'
            "Добро пожаловать на Ticketbag – Ваш партнер в каждом путешествии!\n\n"
             "На TicketBag Вы найдете партнеров для перевозки багажа, "
             "и сможете предложить свободное место в вашем багаже другим пользователям.\n\n"
             "Чтобы добавить маршрут используй @Ticketbag_bot\n",
             parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Посетить группу в VK",
        url="https://vk.com/ticketbag")
    )
    builder.row(InlineKeyboardButton(
        text="Посетить канал в Telegram",
        url="https://t.me/ticketbag")
    )
    builder.row(InlineKeyboardButton(
        text="Посетить наш сайт",
        url="https://ticketbag.info")
    )
    await msg.answer(
        "Подписывайся на нас: 👇👇",
        reply_markup=builder.as_markup()
    )


@dp.message(Command("start"))
async def start_handler(msg: Message):
    if msg.from_user.last_name is not None:
        await msg.answer(f'Привет, {msg.from_user.first_name} {msg.from_user.last_name}! 👋\n'
                          "Чтобы добавить маршрут перейди по ссылке /add_route\n",
                         parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    else:
        await msg.answer(f'Привет, {msg.from_user.first_name}! 👋\n'
                         "Чтобы добавить маршрут перейди по ссылке /add_route\n",
                         parse_mode=ParseMode.HTML, disable_web_page_preview=True)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
