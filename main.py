import csv
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

ua = UserAgent(min_percentage=10)

url = 'https://parsinger.ru/html/index1_page_1.html'
response = requests.get(url=url)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'lxml')

headlines = [
	'Наименование', 'Артикул', 'Бренд', 'Модель',
	'Наличие', 'Цена', 'Старая цена', 'Ссылка'
]


session = requests.Session()

def get_links_card(soup):
	pagen = int(soup.find('div', 'pagen').find_all('a')[-1].text)
	category = [f"https://parsinger.ru/html/{x['href']}" for x in soup.find('div', 'nav_menu').find_all('a')]
	items_url = []
	for x in range(1, len(category) + 1):
		for i in range(1, pagen + 1):
			try:
				page_url = f'https://parsinger.ru/html/index{x}_page_{i}.html'
				req = session.get(url=page_url, headers={'User-Agent': ua.random})
				if req.status_code == 200:
					req.encoding = 'utf-8'
					soup1 = BeautifulSoup(req.text, 'lxml')
					for url in [f"https://parsinger.ru/html/{x['href']}" for x in soup1.find_all('a', class_='name_item')]:
						items_url.append(url)
			except requests.HTTPError as e:
				return f'Error in function: {req.status_code}\n{e}'

	return items_url


with open('all_items_card.csv', 'w', newline='', encoding='utf-8-sig') as file:
	writer = csv.writer(file, delimiter=';')
	writer.writerow(headlines)

with open('all_items_card.csv', 'a', newline='', encoding='utf-8-sig') as file:
	writer = csv.writer(file, delimiter=';')
	for url in get_links_card(soup):
		try:
			req = session.get(url=url, headers={'User-Agent': ua.random})
			req.encoding = 'utf-8'
			card_soup = BeautifulSoup(req.text, 'lxml')

			if req.status_code == 200:
				name = card_soup.find('p', id='p_header').text.strip()
				article = card_soup.find('p', class_='article').text.strip().split(': ')[1]
				brand = card_soup.find('li', id='brand').text.strip().split(': ')[1]
				model = card_soup.find('li', id='model').text.strip().split(': ')[1]
				in_stock = card_soup.find('span', id='in_stock').text.strip().split(': ')[1]
				price = card_soup.find('span', id='price').text.strip()
				old_price = card_soup.find('span', id='old_price').text.strip()
				link = url

				writer.writerow([
					name, article, brand, model,
					in_stock, price, old_price, link
				])
		except requests.HTTPError as e:
			print(f'Error: {req.status_code}\n{e}')
