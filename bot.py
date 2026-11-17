
import os
import asyncio
import logging
import random
import sqlite3
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

load_dotenv()
MY_TOKEN = os.getenv("token")

bot = Bot(token=MY_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)


def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            login TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_login = State()
    waiting_for_password = State()


class SearchStates(StatesGroup):
    waiting_for_login = State()


@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "Привет! Доступные команды:\n"
        "/удача — проверить удачу\n"
        "/reg — зарегистрироваться\n"
        "/find — найти пользователя по логину"
    )


@dp.message(Command("удача"))
async def task_luck(message: Message):
    number = random.randint(1, 12)

    if number in (3, 9, 12):
        await message.answer(f"{number} — Победитель")
    else:
        await message.answer(f"{number} — Попытайся еще раз")


@dp.message(Command("reg"))
async def cmd_register(message: Message, state: FSMContext):
    await state.set_state(RegistrationStates.waiting_for_name)
    await message.answer("Введите ваше имя:")


@dp.message(Command("find"))
async def cmd_find(message: Message, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_login)
    await message.answer("Введите логин для поиска:")


@dp.message(RegistrationStates.waiting_for_name)
async def process_reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(RegistrationStates.waiting_for_login)
    await message.answer("Введите логин:")


@dp.message(RegistrationStates.waiting_for_login)
async def process_reg_login(message: Message, state: FSMContext):
    await state.update_data(login=message.text)
    await state.set_state(RegistrationStates.waiting_for_password)
    await message.answer("Введите пароль:")


@dp.message(RegistrationStates.waiting_for_password)
async def process_reg_password(message: Message, state: FSMContext):
    data = await state.get_data()

    name = data.get("name")
    login = data.get("login")
    password = message.text

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (name, login, password) VALUES (?, ?, ?)",
            (name, login, password)
        )
        conn.commit()
        await message.answer("Регистрация успешно завершена!")
    except sqlite3.IntegrityError:
        await message.answer("Пользователь с таким логином уже существует.")

    conn.close()
    await state.clear()


@dp.message(SearchStates.waiting_for_login)
async def process_search_login(message: Message, state: FSMContext):
    login_to_find = message.text

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM users WHERE login = ?",
        (login_to_find,)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        await message.answer(f"Имя пользователя: {result[0]}")
    else:
        await message.answer("Пользователь не найден")

    await state.clear()


@dp.message(F.text.func(lambda text: text.isdigit()))
async def task_square(message: Message):
    number = int(message.text)
    square = number ** 2
    await message.answer(str(square))


@dp.message(F.text.func(lambda text: text.lower() == "chumba"))
async def task_name_greeting(message: Message):
    await message.answer("Тебя зовут ChumBa")


@dp.message(F.text)
async def task_uppercase(message: Message):
    await message.answer(message.text.upper())


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
