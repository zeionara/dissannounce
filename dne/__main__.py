import re
import os

from pathlib import Path
from http import HTTPStatus
from click import group, argument, option
from requests import Session
from bs4 import BeautifulSoup
from tqdm import tqdm
from pandas import DataFrame, read_csv, set_option

from .Status import Status


PAGES_PATH = 'assets/pages'
STATS_PATH = 'assets/stats.tsv'

STATUS_PATTERN = re.compile('.*Статус защиты.*')
DISSOVET_PATTERN = re.compile('.*Диссертационный совет:.*')
SPECIALITY_PATTERN = re.compile('.*Специальность:.*')


@group()
def main():
    pass


def extract_prop(bs: BeautifulSoup, pattern: re.Pattern) -> str | None:
    candidates = bs.find_all('strong', string = pattern)

    if len(candidates) < 1:
        return None

    parent = candidates[0].parent
    candidates[0].decompose()

    return parent.text.strip()


def extract_status(bs: BeautifulSoup):
    return Status(extract_prop(bs, STATUS_PATTERN))


def extract_dissovet(bs: BeautifulSoup):
    dissovet = extract_prop(bs, DISSOVET_PATTERN)

    return dissovet[::-1].split(' ', maxsplit = 1)[0][::-1]


def extract_speciality(bs: BeautifulSoup):
    speciality = extract_prop(bs, SPECIALITY_PATTERN)
    speciality = speciality.split('\n', maxsplit = 1)[0]

    if speciality.endswith('.'):
        return speciality[:-1]

    return speciality


def extract_heading(bs: BeautifulSoup):
    bs = bs.find('div', class_ = 'dissertation__wrapper')

    return bs.find('h2', class_ = 'dissertation-heading').text.strip().capitalize()


def extract_supervisor(bs: BeautifulSoup):
    bs = bs.find('div', class_ = 'dissertation__wrapper')

    return bs.find('h3', class_ = 'person__card-heading').text.strip()


def agregate(path: str, column: str):
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


@main.group()
def list():
    pass


@list.command()
@argument('stats-path', type = str, default = STATS_PATH)
@option('-n', type = int, default = 10)
def speciality(stats_path: str, n: int):
    df = agregate(stats_path, column = 'speciality')
    print(df.head(n))


@list.command()
@argument('stats-path', type = str, default = STATS_PATH)
@option('-n', type = int, default = 10)
def dissovet(stats_path: str, n: int):
    df = agregate(stats_path, column = 'dissovet')
    print(df.head(n))


@list.command()
@argument('stats-path', type = str, default = STATS_PATH)
@option('-n', type = int, default = 10)
def supervisor(stats_path: str, n: int):
    df = agregate(stats_path, column = 'supervisor')
    print(df.head(n))


@main.command()
@argument('pages-path', type = str, default = PAGES_PATH)
@argument('stats-path', type = str, default = STATS_PATH)
def stats(pages_path: str, stats_path: str):
    records = []

    for file in os.listdir(pages_path):
        if file.endswith('html'):
            with open(os.path.join(pages_path, file), 'r') as file_handler:
                bs = BeautifulSoup(file_handler.read(), features = 'html.parser')

            records.append(
                {
                    'id': Path(file).stem,
                    'successful': extract_status(bs).bool,
                    'dissovet': extract_dissovet(bs),
                    'speciality': extract_speciality(bs),
                    'title': extract_heading(bs),
                    'supervisor': extract_supervisor(bs)
                }
            )

    df = DataFrame.from_records(records, index = 'id')
    df.to_csv(stats_path, sep = '\t')


# @argument('offset', type = int, default = 0)
# @argument('n-pages', type = int, default = 1000)
@main.command()
@argument('numbers-path', type = str, default = 'assets/numbers.txt')
@argument('pages-path', type = str, default = PAGES_PATH)
# def pull(numbers_path: str, destination_path: str, offset: int, n_pages: int):
def pull(numbers_path: str, pages_path: str):
    session = Session()

    with open(numbers_path, 'r', encoding = 'utf-8') as file:
        numbers = [int(line[:-1]) for line in file.readlines()]

    n_missing = 0

    pbar = tqdm(numbers, desc = 'Missing 0 disertations')
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

            # bs = BeautifulSoup(result.text)

            # print(bs)


if __name__ == '__main__':
    set_option('display.max_rows', None)
    main()
