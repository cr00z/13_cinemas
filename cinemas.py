import requests
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import argparse
import logging
import itertools


AFISHA = 'https://www.afisha.ru/msk/schedule_cinema/'
KINOPOISK = 'https://www.kinopoisk.ru/'
KINOPOISK_SEARCH = '{}index.php'.format(KINOPOISK)
FREEPROXY_API_URL = 'http://www.freeproxy-list.ru/api/proxy'
FREEPROXY_API_PARAMS = {'anonymity': 'false', 'token': 'demo'}


'''
1. 'этот код может никогда не закончиться...' - или будет результат или
закончатся валидные прокси
2. Я не нашел реализацию пула с сохранением позиции и возможностью модификации.
Для itertools.cycle все равно нужно дописать функционал для удаления
неработающих прокси, а это только через создание нового итератора
(соответственно позиция next слетает)
'''


def get_logger(logfile_name):
    logging.basicConfig(filename=logfile_name, filemode='w', level=logging.DEBUG)
    return logging.getLogger('cinemas')


def fetch_page(url, params=None, proxy=None):
    proxy_timeout = 10
    try:
        return requests.get(
            url,
            params=params,
            headers={'User-agent': str(UserAgent().random)},
            proxies={'https': 'https://{}'.format(proxy)} if proxy else None,
            timeout=proxy_timeout
        ).content
    except requests.exceptions.RequestException:
        return None


def parse_afisha_list(raw_html):
    skip_items = 2
    afisha_soup = BeautifulSoup(raw_html, 'lxml')
    for film_meta in afisha_soup.find_all('meta', itemprop='name')[skip_items:]:
        yield film_meta['content']


def get_soup(raw_html):
    try:
        return BeautifulSoup(raw_html, 'lxml')
    except TypeError:
        return None


def find_info_in_soup(soup, tag, tag_param, next_sibling=False):
    try:
        soup_tag = soup.find(tag, tag_param)
        if next_sibling:
            soup_tag = soup_tag.next_sibling
        return soup_tag.text
    except AttributeError:
        return None


def find_kinopoisk_movie_url(movie_title, proxy):
    raw_html = fetch_page(
        KINOPOISK_SEARCH,
        params={'kp_query': movie_title},
        proxy=proxy
    )
    kp_soup = get_soup(raw_html)
    if kp_soup is None:
        return None
    try:
        data_url = kp_soup.find('a', {'class': 'js-serp-metrika'})['data-url']
        return re.search(r'film/\d*', data_url)[0]
    except AttributeError:
        return None


def find_kinopoisk_movie_info(movie_url, proxy):
    nbsp_char = '\xa0'
    raw_html = fetch_page('{}{}'.format(KINOPOISK, movie_url), proxy=proxy)
    kp_soup = get_soup(raw_html)
    if kp_soup is None:
        return None
    movie_votes_str = find_info_in_soup(kp_soup, 'span', {'class': 'ratingCount'})
    movie_rating_str = find_info_in_soup(kp_soup, 'span', {'class': 'rating_ball'})
    if not movie_rating_str:
        movie_votes_str = find_info_in_soup(
                kp_soup,
                'span',
                {'title': 'Рейтинг скрыт (недостаточно оценок)'},
                next_sibling=True
        )
        movie_rating_str = '0'
        if not movie_votes_str:
            return None
    return (
        float(movie_rating_str),
        int(movie_votes_str.replace(nbsp_char, ''))
    )


def get_kinopoisk_info_callback(callback_func, url, proxies_pool, script_log):
    for proxy in proxies_pool:
        script_log.debug('Check: {}'.format(proxy))
        return_value = callback_func(url, proxy)
        if return_value:
            return return_value


def get_kinopoisk_info(movie_title, proxies_pool, script_log):
    script_log.debug(movie_title)
    movie_url = get_kinopoisk_info_callback(
        find_kinopoisk_movie_url,
        movie_title,
        proxies_pool,
        script_log
    )
    script_log.debug(movie_url)
    movie_rating = get_kinopoisk_info_callback(
        find_kinopoisk_movie_info,
        movie_url,
        proxies_pool,
        script_log
    ) or (0, 0)
    script_log.debug(movie_rating)
    return (movie_title, movie_rating[0], movie_rating[1])


def output_movies_to_console(movies, limit):
    for movie in movies[:limit]:
        print(*movie)


def get_cmdline_args():
    parser = argparse.ArgumentParser(
        description='Simple console script to select a movie'
    )
    parser.add_argument('--limit', type=int, default=10, help='num of films')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_cmdline_args()
    script_log = get_logger('cinemas.log')
    proxies_pool = fetch_page(
        FREEPROXY_API_URL,
        FREEPROXY_API_PARAMS
    ).decode('utf-8').split('\n')
    movies = [get_kinopoisk_info(movie_title, proxies_pool, script_log)
        for movie_title in parse_afisha_list(fetch_page(AFISHA))]
    movies.sort(key=lambda i: i[1], reverse=True)
    output_movies_to_console(movies, args.limit)
