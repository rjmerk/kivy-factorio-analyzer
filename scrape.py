from bs4 import BeautifulSoup
import requests
import re

from sql import save_scraped_recipe, show_assembler_ratios

PARSER = 'lxml'
DOMAIN = 'https://wiki.factorio.com'
URL_SCIENCE_PACKS = '/Category:Science_packs'


def main():
    show_assembler_ratios()
    return
    links = links_parsed_from(fetched_page(URL_SCIENCE_PACKS))
    visited_links = set()
    while links:
        link = links.pop()
        recipe = parse_recipe_from(fetched_page(link))
        save_scraped_recipe(recipe)
        visited_links.add(link)
        for input in recipe['inputs']:
            new_link = input.get('link')
            if new_link is not None and new_link not in visited_links:
                links.append(new_link)


def fetched_page(url):
    page = requests.get(DOMAIN + url)
    page.raise_for_status()
    return page.text


def links_parsed_from(html):
    soup = BeautifulSoup(html, PARSER)
    category_div = soup.find('div', class_='mw-category')
    return [
        link.get('href')
        for link in category_div.find_all('a')
        if ':' not in link.get('href')
        and 'archive' not in link.get('href')
    ]


def parse_recipe_from(html):
    soup = BeautifulSoup(html, PARSER)
    name = soup.find(id='firstHeading').string
    produced_by = find_produced_by(soup)
    sidebar = soup.find(class_='tabbertab')
    if not sidebar:
        return {
            'output_name': name,
            'time': 1,
            'inputs': [],
            'output_amount': 1,
            'produced_by': produced_by,
        }

    recipe_block = (
        sidebar
        .find('table')
        .find_all('tr')[1]
    )
    subcomponents = (
        recipe_block
        .find_all('div', class_='factorio-icon')
    )
    time = float(
        subcomponents[0]
        .find('div', class_='factorio-icon-text')
        .string
    )
    inputs = [
        {
            'name':  n.find('a')['title'],
            'amount': n.find('div', class_='factorio-icon-text').string,
            'link': n.find('a')['href'],
        }
        for n in subcomponents[1:-1]
    ]
    output = (
        subcomponents[-1]
        .find('div', class_='factorio-icon-text')
        .string
    )
    return {
        'output_name': name,
        'time': time,
        'inputs': inputs,
        'output_amount': output,
        'produced_by': produced_by,
    }


def find_produced_by(soup):
    try:
        production_row = (
            soup.find(class_='infobox')
            .find("p", string=re.compile('Produced by'))
            .find_parent('tr')
            .find_next('tr'))
    except AttributeError:
        return 'unknown'

    if production_row is None:
        return 'unknown'
    elif (production_row
          .find('a', href=re.compile('/Assembling_machine_')) is not None):
        return "assembler"
    elif production_row.find('a', href=re.compile("/.*furnace")) is not None:
        return 'furnace'
    elif production_row.find('a', href="/Chemical_plant") is not None:
        return 'chemical_plant'
    elif production_row.find('a', href="/Electric_mining_drill") is not None:
        return 'mining'
    elif production_row.find('a', href="/Oil_refinery") is not None:
        return 'refinery'
    else:
        return 'unknown'


if __name__ == '__main__':
    main()
