# Cinemas

Simple console script to select a movie.

The script outputs most popular movies sorted by rating.

It receives a list of new movies from [Afisha](https://www.afisha.ru/msk/schedule_cinema/) and gets a rating and a number of votes for each film from [Kinopoisk](https://www.kinopoisk.ru/).

You can use *--limit* key to output a certain amount of movies (default 10).

# How to Install

Python 3 should be already installed. 

Script use:
* [requests](https://pypi.org/project/requests/2.21.0/)
* [beautifulsoup4](https://pypi.org/project/beautifulsoup4/4.5.1/)
* [lxml](https://pypi.org/project/lxml/4.3.3/)
* [fake-useragent](https://pypi.org/project/fake-useragent/0.1.11/)

Then use pip (or pip3 if there is a conflict with old Python 2 setup) to install dependencies:

```bash
pip install -r requirements.txt # alternatively try pip3
```

Remember, it is recommended to use [virtualenv/venv](https://devman.org/encyclopedia/pip/pip_virtualenv/) for better isolation.

# Quickstart

Example of script launch on Linux, Python 3.5:

```bash

$ python cinemas.py --limit 2
Мстители: Финал 8.004 80299
Коридор бессмертия 0 0

```

Use in Windows similarly.

# Project Goals

The code is written for educational purposes. Training course for web-developers - [DEVMAN.org](https://devman.org)
