import os
import asyncio
import random
import config
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)


class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(config.TOKEN).build()
        self._register_handlers()
        self.user_states: Dict[int, Dict] = {}  # Хранение состояний пользователей
        self.translation_directions: Dict[int, str] = {}  # Направления перевода для каждого пользователя

    def _register_handlers(self):
        """Регистрация всех обработчиков команд"""
        handlers = [
            CommandHandler("start", self._start),
            CommandHandler("time", self._handle_time),
            CommandHandler("date", self._handle_date),
            CommandHandler("dice", self._handle_dice),
            CommandHandler("geocode", self._handle_geocode),
            CommandHandler("quiz", self._start_quiz),
            CommandHandler("translate", self._handle_translate),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text),
            CallbackQueryHandler(self._handle_callback)
        ]
        for handler in handlers:
            self.application.add_handler(handler)

    # Основные команды
    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            ['⏱ Время', '📅 Дата'],
            ['🎲 Кубик', '🗺 Геокодер'],
            ['❓ Викторина', '🌍 Переводчик']
        ]
        await update.message.reply_text(
            "Выберите функцию:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )

    async def _handle_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(f"Текущее время: {datetime.now().strftime('%H:%M:%S')}")

    async def _handle_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(f"Сегодня: {datetime.now().strftime('%Y-%m-%d')}")

    # Игральные кости (Задание №7)
    async def _handle_dice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            [InlineKeyboardButton("1d6", callback_data="dice_1d6"),
             InlineKeyboardButton("2d6", callback_data="dice_2d6")],
            [InlineKeyboardButton("1d20", callback_data="dice_1d20")]
        ]
        await update.message.reply_text(
            "Выберите кубик:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Геокодер с Yandex API (Задание №10)
    async def _handle_geocode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not context.args:
            await update.message.reply_text("Использование: /geocode <место>")
            return

        query = " ".join(context.args)
        try:
            # Запрос к Yandex Geocoder API
            geocoder_url = f"https://geocode-maps.yandex.ru/1.x/?apikey={config.YANDEX_GEOCODER_API}&geocode={query}&format=json"
            response = requests.get(geocoder_url).json()

            feature = response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
            pos = feature['Point']['pos']
            lon, lat = pos.split()
            address = feature['metaDataProperty']['GeocoderMetaData']['text']

            # Получаем статическую карту
            map_url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&spn=0.05,0.05&l=map&pt={lon},{lat},pm2rdm"

            await update.message.reply_photo(
                photo=map_url,
                caption=f"📍 {address}\n\nКоординаты: {lat}, {lon}"
            )
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}")

    # Викторина (Задание №9)
    async def _start_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        questions = [
            {"question": "Столица России?", "answer": "Москва"},
            {"question": "2+2?", "answer": "4"}
        ]
        random.shuffle(questions)

        self.user_states[update.effective_user.id] = {
            'questions': questions[:5],
            'current': 0,
            'score': 0
        }

        await self._ask_question(update)

    async def _ask_question(self, update: Update) -> None:
        user_id = update.effective_user.id
        state = self.user_states[user_id]

        if state['current'] < len(state['questions']):
            question = state['questions'][state['current']]['question']
            await update.message.reply_text(f"Вопрос {state['current'] + 1}: {question}")
        else:
            await update.message.reply_text(
                f"Викторина завершена! Ваш результат: {state['score']}/{len(state['questions'])}"
            )
            del self.user_states[user_id]

    # Переводчик с Yandex API (Задание №11)
    async def _handle_translate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды перевода"""
        keyboard = [
            [InlineKeyboardButton("🇷🇺 → 🇬🇧 Русский-Английский", callback_data="translate_ru-en")],
            [InlineKeyboardButton("🇬🇧 → 🇷🇺 Английский-Русский", callback_data="translate_en-ru")],
        ]
        await update.message.reply_text(
            "Выберите направление перевода:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def _translate_text(self, text: str, direction: str) -> str:
        """Функция перевода текста через Yandex Translate API"""
        try:
            url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
            headers = {
                "Authorization": f"Api-Key {config.YANDEX_TRANSLATE_API}",
                "Content-Type": "application/json"
            }
            data = {
                "texts": [text],
                "targetLanguageCode": direction.split('-')[1]
            }

            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            return result['translations'][0]['text']
        except Exception as e:
            return f"Ошибка перевода: {str(e)}"

    # Обработчики сообщений и колбэков
    async def _handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        text = update.message.text

        # Обработка ответов на викторину
        if user_id in self.user_states:
            state = self.user_states[user_id]
            correct_answer = state['questions'][state['current']]['answer']

            if text.lower() == correct_answer.lower():
                state['score'] += 1
                await update.message.reply_text("✅ Правильно!")
            else:
                await update.message.reply_text(f"❌ Неправильно! Правильный ответ: {correct_answer}")

            state['current'] += 1
            await self._ask_question(update)

        # Обработка текста для перевода
        elif user_id in self.translation_directions:
            direction = self.translation_directions[user_id]
            translated = await self._translate_text(text, direction)
            await update.message.reply_text(f"Перевод:\n{translated}")

        # Обработка обычных текстовых команд
        else:
            if text == '⏱ Время':
                await self._handle_time(update, context)
            elif text == '📅 Дата':
                await self._handle_date(update, context)
            elif text == '🎲 Кубик':
                await self._handle_dice(update, context)
            elif text == '🗺 Геокодер':
                await update.message.reply_text("Используйте /geocode <место>")
            elif text == '❓ Викторина':
                await self._start_quiz(update, context)
            elif text == '🌍 Переводчик':
                await self._handle_translate(update, context)
            else:
                await update.message.reply_text(f"Вы сказали: {text}")

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        # Обработка кубиков
        if query.data.startswith("dice_"):
            dice_type = query.data.split("_")[1]
            if dice_type == "1d6":
                result = random.randint(1, 6)
            elif dice_type == "2d6":
                result = f"{random.randint(1, 6)} и {random.randint(1, 6)}"
            elif dice_type == "1d20":
                result = random.randint(1, 20)

            await query.edit_message_text(text=f"🎲 Результат: {result}")

        # Обработка выбора направления перевода
        elif query.data.startswith("translate_"):
            direction = query.data.split("_")[1]
            self.translation_directions[user_id] = direction
            await query.edit_message_text(
                text=f"Выбрано направление: {direction}\nОтправьте текст для перевода"
            )

    def run(self):
        """Запуск бота"""
        try:
            if os.name == 'nt':
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            self.application.run_polling()
        except KeyboardInterrupt:
            print("Бот остановлен")
        finally:
            if self.application.running:
                self.application.stop()


def main():
    bot = TelegramBot()
    bot.run()


if __name__ == '__main__':
    main()