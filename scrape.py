from bs4 import BeautifulSoup
import requests

PARSER = 'lxml'

DOMAIN = 'https://wiki.factorio.com'
URL_INTERMEDIATE_PRODUCTS = '/Category:Intermediate_products'


def main():
    links = scrape_links_for_intermediate_products()
    for link in links:
        data = scrape_component_data(link)
        print(data)
        print("=========================")


def scrape_links_for_intermediate_products():
    page = requests.get(DOMAIN + URL_INTERMEDIATE_PRODUCTS)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, PARSER)
    category_div = soup.find('div', class_='mw-category')
    return [
        link.get('href')
        for link in category_div.find_all('a')
        if ':' not in link.get('href')
        and 'archive' not in link.get('href')
    ]


def scrape_component_data(link):
    page = requests.get(DOMAIN + link)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, PARSER)
    name = soup.find(id='firstHeading').string
    sidebar = soup.find(class_='tabbertab')
    if sidebar:
        return scrape_component_with_recipe(name, sidebar)
    else:
        return {
            'name': name,
            'time': -1,
            'inputs': [],
            'output_amount': 1
        }


def scrape_component_with_recipe(name, sidebar):
    recipe_block = (
        sidebar
        .find('table')
        .find_all('tr')[1]
    )
    subcomponents = (
        recipe_block
        .find_all('div', class_='factorio-icon')
    )
    time = (
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
        'name': name,
        'time': time,
        'inputs': inputs,
        'output_amount': output
    }


if __name__ == '__main__':
    main()
