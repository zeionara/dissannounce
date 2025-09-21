import re

from bs4 import BeautifulSoup

from .Status import Status


STATUS_PATTERN = re.compile('.*Статус защиты.*')
DISSOVET_PATTERN = re.compile('.*Диссертационный совет:.*')
SPECIALITY_PATTERN = re.compile('.*Специальность:.*')
UPLOAD_DATE_PATTERN = re.compile('.*Дата размещения диссертации:.*')
DEFENCE_DATE_PATTERN = re.compile('.*Дата защиты:.*')


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


def extract_upload_date(bs: BeautifulSoup):
    return extract_prop(bs, UPLOAD_DATE_PATTERN)


def extract_defence_date(bs: BeautifulSoup):
    return extract_prop(bs, DEFENCE_DATE_PATTERN)


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


def extract_author(bs: BeautifulSoup):
    bs = bs.find('section', class_ = 'dissertation-description')

    return bs.find('h3', class_ = 'person__card-heading').text.strip()
