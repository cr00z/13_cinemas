import requests
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent


AFISHA = 'https://www.afisha.ru/msk/schedule_cinema/'
KINOPOISK = 'https://www.kinopoisk.ru/'
KINOPOISK_SEARCH = KINOPOISK + 'index.php?kp_query='
FREEPROXY_API = 'http://www.freeproxy-list.ru/api/proxy?anonymity=false&token=demo'


class ProxyPool:
    __current = -1;
    __pool = []
    
    def __init__(self):
        self.__pool = fetch_page(FREEPROXY_API).decode('utf-8').split('\n')

    def next(self):
        if len(self.__pool) <= 0:
            return None
        self.__current += 1
        if self.__current >= len(self.__pool):
            self.__current = 0
        return self.__pool[self.__current]
    
    def remove(self):
        if self.__current >= len(self.__pool):
            return None
        
        
        
def fetch_page(url, proxy=None):
    proxy_timeout = 10
    try:
        return requests.get(
            url,
            headers={'User-agent': str(UserAgent().random)},
            proxies={'https': 'https://' + proxy} if proxy else None,
            timeout=proxy_timeout
        ).content
    except (
        requests.exceptions.ProxyError,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.SSLError
    ):
        return None
    


def parse_afisha_list(raw_html):
    SKIP_ITEMS = 2
    afisha_soup = BeautifulSoup(raw_html, 'lxml')
    for film_meta in afisha_soup.find_all('meta', itemprop='name')[SKIP_ITEMS:]:
        yield film_meta['content']


def find_kinopoisk_movie_url(movie_title, proxies_pool):
    raw_html = fetch_page(KINOPOISK_SEARCH + movie_title)
    kp_soup = BeautifulSoup(raw_html, 'lxml')
    data_url = kp_soup.find('a', {'class': 'js-serp-metrika'})['data-url']
    return re.search(r'film/\d*', data_url)[0]


def fetch_movie_info(movie_url, proxy):
    NOBREAK_SPACE = '\xa0'
    try:
        raw_html = fetch_page(KINOPOISK + movie_url, proxy)
    except (
        requests.exceptions.ProxyError,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.SSLError
    ):
        return None
    kp_soup = BeautifulSoup(raw_html, 'lxml')
    return (
        kp_soup.find('span', {'class': 'rating_ball'}).text,
        kp_soup.find('span', {'class': 'ratingCount'}).text.replace(NOBREAK_SPACE, '')
    )


def output_movies_to_console(movies):
    pass


if __name__ == '__main__':
    proxies = get_freeproxy_list()
    if not proxies:
        exit('freeproxy list not ready')
    current_proxy = 0
    for movie_title in parse_afisha_list(fetch_page(AFISHA)):
        movie_url = find_kinopoisk_movie_url(movie_title)
        print(movie_title, movie_url)
        while len(proxies):
            rating = fetch_movie_info(movie_url, proxies[current_proxy])
            if not rating:
                remove_proxy = proxies.pop(current_proxy)
                print(remove_proxy)
            else:
                current_proxy = current_proxy + 1
                if current_proxy == len(proxies):
                    current_proxy = 0
                break
        print(rating)