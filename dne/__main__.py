import os
from time import sleep

from pathlib import Path
from http import HTTPStatus
from click import group, argument
from requests import Session
from bs4 import BeautifulSoup
from tqdm import tqdm
from pandas import DataFrame, read_csv, set_option
from datetime import datetime

from .extraction import extract_status, extract_dissovet, extract_speciality, extract_heading, extract_supervisor, extract_upload_date, extract_defence_date, extract_author, extract_download_link


PAGES_PATH = 'assets/pages'
STATS_PATH = 'assets/stats.tsv'


@group()
def main():
    pass


def top(path: str, column: str):
    df = (
        read_csv(path, sep = '\t')
        .groupby(column)
        .size()
        .sort_values(ascending = False)
        .reset_index(name='count')
    )

    df = df.assign(
        rank = range(1, len(df) + 1),
        cumulative_count = df['count'].cumsum(),
        percentile = lambda x: x['cumulative_count'] / x['count'].sum() * 100
    )[
        ['rank', column, 'count', 'percentile']
    ].set_index('rank')

    df.index.name = None

    return df


def match(path: str, column: str, pattern: str):
    df = read_csv(path, sep = '\t')
    df = df[df[column].str.contains(pattern, regex = True, na = False)]
    df.index = range(1, len(df) + 1)

    return df


@main.group()
def speciality():
    pass


@main.group()
def dissovet():
    pass


@main.group()
def supervisor():
    pass


@main.group()
def author():
    pass


@speciality.command(name = 'top')
@argument('n', type = int, default = 10)
@argument('stats-path', type = str, default = STATS_PATH)
def speciality_top(n: int, stats_path: str):
    print(
        top(stats_path, column = 'speciality').head(n)
    )


@speciality.command(name = 'match')
@argument('pattern', type = str, default = '.*')
@argument('stats-path', type = str, default = STATS_PATH)
def speciality_match(pattern: str, stats_path: str):
    print(
        match(stats_path, column = 'speciality', pattern = pattern)
    )


@dissovet.command(name = 'top')
@argument('n', type = int, default = 10)
@argument('stats-path', type = str, default = STATS_PATH)
def dissovet_top(n: int, stats_path: str):
    print(
        top(stats_path, column = 'dissovet').head(n)
    )


@dissovet.command(name = 'match')
@argument('pattern', type = str, default = '.*')
@argument('stats-path', type = str, default = STATS_PATH)
def dissovet_match(pattern: str, stats_path: str):
    print(
        match(stats_path, column = 'dissovet', pattern = pattern)
    )


@supervisor.command(name = 'top')
@argument('n', type = int, default = 10)
@argument('stats-path', type = str, default = STATS_PATH)
def supervisor_top(n: int, stats_path: str):
    print(
        top(stats_path, column = 'supervisor').head(n)
    )


@supervisor.command(name = 'match')
@argument('pattern', type = str, default = '.*')
@argument('stats-path', type = str, default = STATS_PATH)
def supervisor_match(pattern: str, stats_path: str):
    print(
        match(stats_path, column = 'supervisor', pattern = pattern)
    )


@author.command(name = 'match')
@argument('pattern', type = str, default = '.*')
@argument('stats-path', type = str, default = STATS_PATH)
def author_match(pattern: str, stats_path: str):
    print(
        match(stats_path, column = 'author', pattern = pattern)
    )


@main.command()
@argument('pages-path', type = str, default = PAGES_PATH)
@argument('stats-path', type = str, default = STATS_PATH)
def stats(pages_path: str, stats_path: str):
    records = []

    for file in os.listdir(pages_path):
        if file.endswith('html'):
            with open(os.path.join(pages_path, file), 'r', encoding = 'utf-8') as file_handler:
                bs = BeautifulSoup(file_handler.read(), features = 'html.parser')

            records.append(
                {
                    'id': Path(file).stem,
                    'successful': extract_status(bs).bool,
                    'dissovet': extract_dissovet(bs),
                    'speciality': extract_speciality(bs),
                    'title': extract_heading(bs),
                    'author': extract_author(bs),
                    'supervisor': extract_supervisor(bs),
                    'uploaded': (upload_date := extract_upload_date(bs)),
                    'defended': (defence_date := extract_defence_date(bs)),
                    'interval': (datetime.strptime(defence_date, '%d.%m.%Y') - datetime.strptime(upload_date, '%d.%m.%Y')).days
                }
            )

    df = DataFrame.from_records(
        sorted(
            records,
            key = lambda record: datetime.strptime(
                record['defended'],
                '%d.%m.%Y'
            ),
            reverse = True
        ), index = 'id'
    )
    df.to_csv(stats_path, sep = '\t')

    df_interval = df['interval']

    q1 = df_interval.quantile(0.05)
    q3 = df_interval.quantile(0.95)

    print(f'Average interval between dissertation upload and defence data is {df_interval[(df_interval >= q1) & (df_interval <= q3)].mean():0.2f} days')


@main.command()
@argument('pages-path', type = str, default = PAGES_PATH)
@argument('stats-path', type = str, default = STATS_PATH)
@argument('texts-path', type = str, default = 'assets/texts')
def download(pages_path: str, stats_path: str, texts_path: str):
    session = Session()

    if not os.path.isdir(texts_path):
        os.makedirs(texts_path)

    df = read_csv(stats_path, sep = '\t')

    for id_ in df.id:
        with open(os.path.join(pages_path, f'{id_}.html'), 'r', encoding = 'utf-8') as file_handler:
            bs = BeautifulSoup(file_handler.read(), features = 'html.parser')

        speciality = extract_speciality(bs)

        speciality_path = os.path.join(texts_path, speciality)

        if not os.path.isdir(speciality_path):
            os.makedirs(speciality_path)

        heading = extract_heading(bs)
        dissertation_path = None

        while dissertation_path is None or len(dissertation_path.encode('utf-8')) >= 255:
            dissertation_path = os.path.join(speciality_path, f'{heading}.pdf')
            heading = heading[:-1]

        if speciality != '05.13.17' or os.path.isfile(dissertation_path):
            continue

        download_link = extract_download_link(bs)

        with open(dissertation_path, 'wb') as file_handler:
            pass

        print(f'Loading {dissertation_path}...')

        response = session.get(download_link, allow_redirects = True)  # These requests are limited!!!

        bs = BeautifulSoup(response.text, features = 'html.parser')

        download_script = bs.find_all('script')[-1]
        download_link = download_script.text.split('"', maxsplit = 2)[1]

        response = session.get(download_link)

        with open(dissertation_path, 'wb') as file_handler:
            file_handler.write(response.content)


@main.command()
@argument('numbers-path', type = str, default = 'assets/numbers.txt')
@argument('pages-path', type = str, default = PAGES_PATH)
def pull(numbers_path: str, pages_path: str):
    session = Session()

    if not os.path.isdir(pages_path):
        os.makedirs(pages_path)

    with open(numbers_path, 'r', encoding = 'utf-8') as file:
        numbers = [int(line[:-1]) for line in file.readlines()]

    n_missing = 0

    pbar = tqdm(numbers, desc = 'Missing 0 dissertations')
    for number in pbar:
        page_path = os.path.join(pages_path, f'{number}.html')

        if os.path.isfile(page_path):
            continue

        response = session.get(
            f'https://dissovet.itmo.ru/dissertation/?number={number}'
        )

        if response.status_code == HTTPStatus.OK:
            with open(page_path, 'w', encoding = 'utf-8') as file:
                file.write(response.text)
        else:
            n_missing += 1
            pbar.set_description(f'Missing {n_missing} pages')

            print(f'Dissertation №{number} is missing - page is not available')


if __name__ == '__main__':
    set_option('display.max_rows', None)
    main()
