from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from aiogram import executor
import asyncio
import db
import requests
from bs4 import BeautifulSoup

bot = Bot('TOKEN')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
good_num = 0


def download_image(url, filename):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return True
    else:
        return False


def get_categories():
    url = 'https://skifmusic.ru'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    menu_items = soup.find_all('div', class_='header-menu__nav-item', attrs={'data-ix': True})
    # Извлекаем текст и ссылки из каждого элемента
    item_info = [{'name': item.find('a').text.strip(), 'link': item.find('a')['href']} for item in menu_items]
    # Разделяем информацию на два массива
    item_names = [item['name'] for item in item_info]
    item_links = [item['link'] for item in item_info]
    return item_names, item_links


def get_good_categories(link):
    response = requests.get('https://skifmusic.ru' + link)
    soup = BeautifulSoup(response.text, 'html.parser')
    categories = soup.find_all('a', class_='catalog-block-menu__item')

    # Извлекаем названия категорий и ссылки на них
    category_info = [{'name': category.find('div', class_='catalog-block-menu__name').text.strip(),
                      'link': category['href']}
                     for category in categories]

    # Разделяем информацию на два массива
    category_names = [info['name'] for info in category_info]
    category_links = [info['link'] for info in category_info]
    return category_names, category_links


def get_goods(link):
    response = requests.get('https://skifmusic.ru' + link)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Извлекаем информацию из каждого элемента
    items = soup.select('.cards-list__item')

    # Создаем списки для хранения данных
    titles = []
    images = []
    prices = []
    links = []

    # Итерируемся по каждому элементу и извлекаем данные
    for item in items:
        title = item.select_one('.product-card__link').text.strip()
        image = item.select_one('.product-card__image img')['src']
        price = item.select_one('.product-card__price').text.strip()
        link = item.select_one('.product-card__link')['href']

        titles.append(title)
        images.append(image)
        prices.append(price)
        links.append(link)
    return titles, images, prices, links


def navigation_button():
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='⬅️', callback_data='prev')
    button2 = types.InlineKeyboardButton(text='➡️', callback_data='next')
    markup.add(button1, button2)
    return markup


@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='Товары🎸', callback_data='goods')
    button2 = types.InlineKeyboardButton(text='О насℹ️', callback_data='info')
    button3 = types.InlineKeyboardButton(text='Контакты🔍', callback_data='contacts')
    markup.add(button1, button2, button3)
    await message.answer("Здравствуйте!🙂 Выберите нужную опцию👇🏻", reply_markup=markup)
    if len(await db.get_id_on_userid(user_id)) == 0:
        await db.add_user(str(user_id), user_name)


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'info')
async def handle_prev(callback_query: types.CallbackQuery):
    await callback_query.message.answer(f'*Кто мы такие?*\n\n'
                                        f'_SKIFMUSIC_ - это крупнейшая сеть по географии присутствия музыкальный '
                                        f'магазинов от города Находки до Санкт-Петербурга, Москвы, Самары, Краснодара, '
                                        f'Казани и многих других. Мы вдохновляем музыкой с 2005 года.\n\n'
                                        f'Подробнее о нас читайте на официальном сайте по ссылке: https://info.skifmusic.ru/company', parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'contacts')
async def handle_prev(callback_query: types.CallbackQuery):
    await callback_query.message.answer(f'*Телефон*\n\n +7-846-226-51-17\n\n*Адрес*\n\nул. Галактионовская, д.102А\n\n'
                                        f'*Почта*\n\n sales@skifmusic.ru — общие вопросы\n '
                                        f'warranty@skifmusic.ru — гарантия или обмен/возврат товара \n'
                                        f'used@skifmusic.ru — выкуп, обмен и комиссия гитар\n\n'
                                        f'Как добраться: https://yandex.ru/maps/-/CDufR8JY', parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'goods')
async def handle_prev(callback_query: types.CallbackQuery):
    names, _ = get_categories()
    markup = types.InlineKeyboardMarkup()
    buttons = []
    i = 0
    for name in names:
        buttons.append(types.InlineKeyboardButton(text=f'{name}', callback_data=f'category_{i}'))
        i += 1
    for button in buttons:
        markup.add(button)
    await callback_query.message.answer(f"Каталог товаров:", reply_markup=markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('category_'))
async def handle_category(callback_query: types.CallbackQuery):
    category_index = int(callback_query.data.split('_')[1])
    names, links = get_categories()
    names_good, links_good = get_good_categories(links[category_index])
    markup = types.InlineKeyboardMarkup()
    buttons = []
    i = 0
    for name in names_good:
        buttons.append(types.InlineKeyboardButton(text=f'{name}', callback_data=f'category-good_{category_index}_{i}'))
        i += 1
    for button in buttons:
        markup.add(button)
    await callback_query.message.answer(f"Подкаталог:", reply_markup=markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('category-good_'))
async def handle_category(callback_query: types.CallbackQuery):
    global good_num
    category_index = int(callback_query.data.split('_')[1])
    category_good_index = int(callback_query.data.split('_')[2])
    names, links = get_categories()
    names_good, links_good = get_good_categories(links[category_index])
    n, im, p, l = get_goods(links_good[category_good_index])
    filename = 'good.jpg'
    if download_image(im[0], filename):
        print(f"Изображение успешно загружено в файл {filename}")
    else:
        print("Не удалось загрузить изображение")
    text = f"Название: {n[0]}\nЦена: {p[0]}\n{'-' * 30}\nСсылка на товар: {l[0]}"
    good_num = 0
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='⬅️', callback_data=f'prev-good_{category_index}_{category_good_index}')
    button2 = types.InlineKeyboardButton(text='➡️', callback_data=f'next-good_{category_index}_{category_good_index}')
    markup.add(button1, button2)
    await callback_query.message.answer_photo(open(filename, 'rb'), caption=text, reply_markup=markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('prev-good_'))
async def handle_category(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    global good_num
    good_num -= 1
    category_index = int(callback_query.data.split('_')[1])
    category_good_index = int(callback_query.data.split('_')[2])
    names, links = get_categories()
    names_good, links_good = get_good_categories(links[category_index])
    n, im, p, l = get_goods(links_good[category_good_index])
    filename = 'good.jpg'
    if download_image(im[good_num], filename):
        print(f"Изображение успешно загружено в файл {filename}")
    else:
        print("Не удалось загрузить изображение")
    await bot.delete_message(chat_id, callback_query.message.message_id)
    text = f"Название: {n[good_num]}\nЦена: {p[good_num]}\n{'-' * 30}\nСсылка на товар: {l[good_num]}"
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='⬅️', callback_data=f'prev-good_{category_index}_{category_good_index}')
    button2 = types.InlineKeyboardButton(text='➡️', callback_data=f'next-good_{category_index}_{category_good_index}')
    markup.add(button1, button2)
    await callback_query.message.answer_photo(open('good.jpg', 'rb'), caption=text, reply_markup=markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('next-good_'))
async def handle_category(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    global good_num
    good_num +=1
    category_index = int(callback_query.data.split('_')[1])
    category_good_index = int(callback_query.data.split('_')[2])
    names, links = get_categories()
    names_good, links_good = get_good_categories(links[category_index])
    n, im, p, l = get_goods(links_good[category_good_index])
    filename = 'good.jpg'
    if download_image(im[good_num], filename):
        print(f"Изображение успешно загружено в файл {filename}")
    else:
        print("Не удалось загрузить изображение")
    await bot.delete_message(chat_id, callback_query.message.message_id)
    text = f"Название: {n[good_num]}\nЦена: {p[good_num]}\n{'-' * 30}\nСсылка на товар: {l[good_num]}"
    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton(text='⬅️', callback_data=f'prev-good_{category_index}_{category_good_index}')
    button2 = types.InlineKeyboardButton(text='➡️', callback_data=f'next-good_{category_index}_{category_good_index}')
    markup.add(button1, button2)
    await callback_query.message.answer_photo(open('good.jpg', 'rb'), caption=text, reply_markup=markup)

@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(
        f'Я не знаю, что ответить на это😕 Если хотите использовать функционал, воспользуйтесь командой /start')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(db.create_database())
    executor.start_polling(dp, skip_updates=True)
