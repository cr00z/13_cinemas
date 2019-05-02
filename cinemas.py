import requests
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent


AFISHA = 'https://www.afisha.ru/msk/schedule_cinema/'
KINOPOISK = 'https://www.kinopoisk.ru/'
KINOPOISK_SEARCH = KINOPOISK + 'index.php?kp_query='
FREEPROXY_API = 'http://www.freeproxy-list.ru/api/proxy?anonymity=false&token=demo'


def fetch_page(url, proxy=None):
    proxies = {'https': 'https://' + proxy} if proxy else None
    user_agent = {'User-agent': str(UserAgent().random)}
    return requests.get(url, headers=user_agent, proxies=proxies).content


def get_freeproxy_list():
    return fetch_page(FREEPROXY_API).decode('utf-8').split('\n')


def parse_afisha_list(raw_html):
    SKIP_ITEMS = 2
    afisha_soup = BeautifulSoup(raw_html, 'lxml')
    for film_meta in afisha_soup.find_all('meta', itemprop='name')[SKIP_ITEMS:]:
        yield film_meta['content']


def find_kinopoisk_movie_url(movie_title):
    raw_html = fetch_page(KINOPOISK_SEARCH + movie_title)
    kp_soup = BeautifulSoup(raw_html, 'lxml')
    data_url = kp_soup.find('a', {'class': 'js-serp-metrika'})['data-url']
    return re.search(r'film/\d*', data_url)[0]


def fetch_movie_info(movie_url, proxy):
    NOBREAK_SPACE = '\xa0'
    raw_html = fetch_page(KINOPOISK + film_url, proxy=proxy)
    kp_soup = BeautifulSoup(raw_html, 'lxml')
    return (
        kp_soup.find('span', {'class': 'rating_ball'}).text,
        kp_soup.find('span', {'class': 'ratingCount'}).text.replace(NOBREAK_SPACE, '')
    )


def output_movies_to_console(movies):
    pass


if __name__ == '__main__':
    proxies = get_freeproxy_list()
    # print(*parse_afisha_list(fetch_page(AFISHA)))
    film_url = find_kinopoisk_movie_url('Зеленая книга')
    for proxy in proxies:
        try:
            rating = fetch_movie_info(film_url, proxy)
            break
        except requests.exceptions.ProxyError:
            print('bad proxy {}'.format(proxy))
    print(rating)