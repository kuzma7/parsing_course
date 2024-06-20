import json
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time

# Инициализирую UserAgent для генерации случайного User-Agent
ua = UserAgent(min_percentage=10)

# Итоговый список для карточек
result_dict_with_card = []

url = 'https://parsinger.ru/html/index2_page_1.html'
site = 'https://parsinger.ru/html/'

# Создаю сессию, к слову, без сессии программа выполнялась в 3 раза медленнее
session = requests.Session()


def get_soup(url: str):
	# Получаем супчик из страницы по url
	try:
		# Выполняем GET-запросы с использованием случайного User-Agent
		response = session.get(url=url, headers={'User-Agent': ua.random})
		response.encoding = 'utf-8'
		# Если ничего не сломалось - возвращаем объект супа
		return BeautifulSoup(response.text, 'lxml')
	except requests.ConnectionError as e:
		print(f'ConnectionError: {e}')
	except requests.exceptions.MissingSchema as e:
		print(f'MissingSchema: {e}')
	except requests.exceptions.HTTPError as e:
		print(f'HTTPError: {e}')
	except requests.RequestException as e:
		print(f'RequestException: {e}')

	return None


def get_categories():
	# Здесь мы получаем список ссылок и названий категорий.
	soup = get_soup(url)
	# Извлечение ссылок на категории и их названий из HTML-кода страницы
	links_categories = [i['href'] for i in soup.find('div', class_='nav_menu').find_all('a', attrs={'href': True})]
	names_categories = [name['id'] for name in soup.find('div', class_='nav_menu').find_all('div')]
	return list(zip(links_categories, names_categories))


def get_pages():
	# Функция для получения всех страниц для каждой категории товаров.
	# Возвращает: Словарь, где ключи - названия категорий, значения - списки URL страниц.
	all_pages = {}
	for category_url, category_name in get_categories():
		soup = get_soup(f'{site}{category_url}')
		# Извлечение URL страниц из HTML-кода страницы с пагинацией
		pages = [f'{site}{page["href"]}' for page in soup.find('div', 'pagen').find_all('a')]
		all_pages[category_name] = pages
	return all_pages


def get_cards():
	# Функция для получения всех карточек товаров для каждой страницы категории.
	# Возвращает: Словарь, где ключи - названия категорий, значения - списки URL карточек товаров.
	cards_and_categories_names = {}
	for category_name, pages in get_pages().items():
		for page_url in pages:
			soup = get_soup(page_url)
			# Извлечение URL карточек товаров из HTML-кода страницы
			for link in soup.find_all('a', class_='name_item'):
				cards_and_categories_names.setdefault(category_name, []).append(link['href'])
	return cards_and_categories_names


def get_info():
	# Функция для сбора информации о товарах, их категориях и записи в JSON-файл.
	# Выводит прогресс выполнения и финальное сообщение о завершении работы.

	with open('mobile_info.json', 'w', encoding='utf-8') as json_file:
		for category_name, cards in get_cards().items():
			print(f'Обрабатываю категорию - {category_name}...')
			for card_link in cards:
				page_url = f'{site}{card_link}'
				soup = get_soup(page_url)
				# Извлекаем информацию из карточки
				name = soup.find('p', id='p_header').text
				article = soup.find('p', class_='article').text.split(': ')[1].strip()

				description = soup.find('ul', id='description').find_all('li')
				li_id = [x['id'] for x in description]
				li_text = [descr.text.split(': ')[1].strip() for descr in description]
				descr_dict = dict(zip(li_id, li_text))

				quantity_in_stock = soup.find('span', id='in_stock').text.split(': ')[1]
				price = soup.find('span', id='price').text
				old_price = soup.find('span', id='old_price').text
				link = page_url

				# Формируем словарь под карточку
				product_info = {
					"categories": category_name,
					"name": name,
					"article": article,
					"description": descr_dict,
					"count": quantity_in_stock,
					"price": price,
					"old_price": old_price,
					"link": link
				}
				result_dict_with_card.append(product_info)

		print(f'Записываю данные в файл...')
		json.dump(result_dict_with_card, json_file, indent=4, ensure_ascii=False)
	print(f'Готово!')


# Замер времени выполнения программы
# Время работы без использования Session() примерно 15 секунд
start = time.perf_counter()
get_info()
end = time.perf_counter()

print(f'Время работы программы: {end - start}')
