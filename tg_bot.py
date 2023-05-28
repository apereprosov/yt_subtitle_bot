import logging
from aiogram.dispatcher.filters.state import State
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from deepl import Translator
from selenium import webdriver
from selenium.webdriver.common.by import By
import time,os

LANGUAGE = State()


def translate(text,lang):
    api_key = '8b743847-b2e7-2279-4650-ebf8dea7685b:fx'

    translator = Translator(api_key)
    return translator.translate_text(text,target_lang=lang).text

# Инициализация бота
bot = Bot(token='6024462006:AAFxuXLaQoGFBn6lPvLrnAD8-DJa_jJijCI')
dp = Dispatcher(bot, storage=MemoryStorage())

def get_subtitles(video_url):
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
    options = webdriver.ChromeOptions()
    options.add_argument(user_agent)
    options.add_argument('--headless')

    with webdriver.Chrome(options=options) as browser:
        try:
            browser.get(video_url)
            time.sleep(1)
            browser.save_screenshot('screenshot.png')
            time.sleep(2)
            reject_cookies = browser.find_element(By.XPATH,'/html/body/ytd-app/ytd-consent-bump-v2-lightbox/tp-yt-paper-dialog/div[4]/div[2]/div[6]/div[1]/ytd-button-renderer[1]/yt-button-shape/button')
            reject_cookies.click()
            browser.save_screenshot('screenshot.png')

            time.sleep(1)
            menu_button = browser.find_element(By.XPATH,'/html/body/ytd-app/div[1]/ytd-page-manager/ytd-watch-flexy/div[5]/div[1]/div/div[2]/ytd-watch-metadata/div/div[2]/div[2]/div/div/ytd-menu-renderer/yt-button-shape')
            menu_button.click()
            browser.save_screenshot('screenshot.png')
            
            elementy = browser.find_elements(By.TAG_NAME,'tp-yt-paper-item')
            elementy[-1].click()
            browser.save_screenshot('screenshot.png')
            
            time.sleep(1)
            captions = browser.find_element(By.ID,'segments-container').text
        except:
            print('Субтитры не найдены')

    subtitles = []
    lines = captions.split('\n')

    for i in range(len(lines)):
        if lines[i].__contains__(':') and all(value.isdigit() for value in lines[i].split(':')):
            try:
                subtitle = lines[i+1]
                subtitles.append(subtitle)
            except:
                print(f'ERROR in line {lines[i+1]}') 
    print(' '.join(subtitles))
    return '\n'.join(subtitles)

# Здесь добавляем словарь с флагами и сокращениями языков
language_flags = {
    '🇬🇧': 'EN-GB',  # Английский
    '🇩🇪': 'DE',  # Немецкий
    '🇫🇷': 'FR',  # Французский
    '🇮🇹': 'IT',  # Итальянский
    '🇪🇸': 'ES',  # Испанский
    '🇳🇱': 'NL',  # Голландский
    '🇵🇹': 'PT',  # Португальский
    '🇷🇺': 'RU',  # Русский
    '🇵🇱': 'PL',  # Польский
    '🇺🇦': 'UK',  # Украинский
    '🇷🇴': 'RO',  # Румынский
    # Добавьте другие флаги и коды языков по необходимости
}

# Логирование
logging.basicConfig(level=logging.INFO)

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    # Отправка приветственного сообщения и инструкций пользователю
    text = "Привет! Я бот для скачивания и перевода субтитров с видео."
    text += "\n\nПожалуйста, отправьте мне ссылку на видео, для которого нужны субтитры."
    await message.reply(text)
    

# Обработчик ссылки на видео
@dp.message_handler(regexp=r'https?://[^\s]+')
async def video_handler(message: types.Message, state: FSMContext):
    video_url = message.text
    # Сохранение ссылки на видео в состояние пользователя
    await state.update_data(video=video_url)
    # Отправка запроса на выбор языка перевода
    reply_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for flag in language_flags.keys():
        reply_keyboard.add(flag)
    await message.reply("Выберите язык перевода:", reply_markup=reply_keyboard)

# Обработчик выбора языка
@dp.message_handler(lambda message: message.text in language_flags.keys(), state=LANGUAGE)
async def language_handler(message: types.Message, state: FSMContext):
    # Получение выбранного языка по флагу
    selected_flag = message.text
    selected_language = language_flags.get(selected_flag)
    # Сохранение выбранного языка в состояние
    await state.update_data(language=selected_language)
    
    # Получение ссылки на видео из состояния
    user_data = await state.get_data()
    video_url = user_data.get('video')
    
    # Здесь добавьте свой код для скачивания субтитров по ссылке video_url
    # и их перевода на выбранный язык selected_language
    
    # Пример кода для скачивания и перевода субтитров с использованием deepl
    subtitles = get_subtitles(video_url)  # Функция для скачивания субтитров
    translated_subtitles = translate(subtitles, selected_language)  # Функция для перевода субтитров
    print(translated_subtitles)
    # Сохранение переведенных субтитров в текстовый файл
    file_path = f'subtitles_{selected_language}.txt'
    with open(file_path, 'a') as file:
        file.write(translated_subtitles)
    
    # Отправка файла субтитров пользователю
    with open(file_path, 'rb') as file:
        await message.reply_document(file)
    
    os.remove(file_path)

    
    # Очистка состояния пользователя
    await message.reply('Спасибо за использование нашего бота!')
    
    # Очистка состояния пользователя
    await start_handler(message)

if __name__ == '__main__':
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)
