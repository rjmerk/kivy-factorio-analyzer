from bs4 import BeautifulSoup
import requests

from sql import save_scraped_data, show_assembler_ratios

PARSER = 'lxml'
DOMAIN = 'https://wiki.factorio.com'
URL_INTERMEDIATE_PRODUCTS = '/Category:Intermediate_products'
URL_SCIENCE_PACKS = '/Category:Science_packs'
URL_RESOURCES = '/Category:Resources'
URL_FLUIDS = '/Category:Fluids'


def main():
    show_assembler_ratios()
    return
    resource_links = links_parsed_from(fetched_page(URL_RESOURCES))
    fluid_links = links_parsed_from(fetched_page(URL_FLUIDS))
    science_links = links_parsed_from(fetched_page(URL_SCIENCE_PACKS))

    recipes = [
        parse_recipe_from(fetched_page(link))
        for link in science_links
    ]
    save_scraped_data(recipes)

    component_links = [
        link
        for link in links_parsed_from(fetched_page(URL_INTERMEDIATE_PRODUCTS))
        if link not in resource_links
        and link not in fluid_links
        and link not in science_links
        and link != '/Space_science_pack'
    ]
    recipes = [
        parse_recipe_from(fetched_page(link))
        for link in component_links
    ]
    save_scraped_data(recipes)


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
    sidebar = soup.find(class_='tabbertab')
    if not sidebar:
        return {
            'output_name': name,
            'time': -1,
            'inputs': [],
            'output_amount': 1
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
            'amount': n.find('div', class_='factorio-icon-text').string
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
        'output_amount': output
    }


if __name__ == '__main__':
    main()
