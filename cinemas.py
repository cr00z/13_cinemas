import requests
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import argparse


AFISHA = 'https://www.afisha.ru/msk/schedule_cinema/'
KINOPOISK = 'https://www.kinopoisk.ru/'
KINOPOISK_SEARCH = KINOPOISK + 'index.php?kp_query='
FREEPROXY_API_URL = 'http://www.freeproxy-list.ru/api/proxy'
FREEPROXY_API_PARAMS = {'anonymity': 'false', 'token': 'demo'}
VERBOSE = False


class ProxyPool:
    __current = -1
    __pool = []
    
    def __init__(self):
        self.__pool = fetch_page(
            FREEPROXY_API_URL,
            FREEPROXY_API_PARAMS
        ).decode('utf-8').split('\n')
        if VERBOSE:
            print('ProxyPool:', *self.__pool, sep='\n')

    def get_next(self):
        if len(self.__pool) <= 0:
            return None
        self.__current += 1
        if self.__current >= len(self.__pool):
            self.__current = 0
        return self.__pool[self.__current]
    
    def remove_current(self):
        if self.__current >= len(self.__pool):
            return None
        return self.__pool.pop(self.__current)


def print_debug_info(debug_info):
    if VERBOSE:
        print(debug_info)


def fetch_page(url, params=None, proxy=None):
    proxy_timeout = 10
    try:
        return requests.get(
            url,
            params=params,
            headers={'User-agent': str(UserAgent().random)},
            proxies={'https': 'https://' + proxy} if proxy else None,
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
    raw_html = fetch_page(KINOPOISK_SEARCH + movie_title, proxy)
    kp_soup = get_soup(raw_html)
    if kp_soup is None:
        return None
    try:
        data_url = kp_soup.find('a', {'class': 'js-serp-metrika'})['data-url']
        return re.search(r'film/\d*', data_url)[0]
    except (TypeError, AttributeError):
        return None


def find_kinopoisk_movie_info(movie_url, proxy):
    nbsp_char = '\xa0'
    raw_html = fetch_page(KINOPOISK + movie_url, proxy)
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


def get_kinopoisk_info_callback(callback_func, url, proxies_pool):
    while True:
        proxy = proxies_pool.get_next()
        if not proxy:
            return None
        print_debug_info('Check: {}'.format(proxy))
        return_value = callback_func(url, proxy)
        if return_value:
            return return_value
        print_debug_info('Remove: {}'.format(proxies_pool.remove_current()))


def output_movies_to_console(movies, limit):
    for movie in movies[:limit]:
        print(*movie)


def get_cmdline_args():
    parser = argparse.ArgumentParser(
        description='Simple console script to select a movie'
    )
    parser.add_argument('--limit', type=int, default=10, help='num of films')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_cmdline_args()
    VERBOSE = args.verbose or False
    proxies_pool = ProxyPool()
    movies = []
    for movie_title in parse_afisha_list(fetch_page(AFISHA)):
        print_debug_info(movie_title)
        movie_url = get_kinopoisk_info_callback(
            find_kinopoisk_movie_url,
            movie_title,
            proxies_pool
        )
        print_debug_info(movie_url)
        movie_rating = get_kinopoisk_info_callback(
            find_kinopoisk_movie_info,
            movie_url,
            proxies_pool
        ) or (0, 0)
        print_debug_info(movie_rating)
        movies.append((movie_title, movie_rating[0], movie_rating[1]))
    movies.sort(key=lambda i: i[1], reverse=True)
    output_movies_to_console(movies, args.limit)
