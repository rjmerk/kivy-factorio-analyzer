from bs4 import BeautifulSoup
import requests

PARSER = 'lxml'

DOMAIN = 'https://wiki.factorio.com'
URL_INTERMEDIATE_PRODUCTS = '/Category:Intermediate_products'
URL_SCIENCE_PACKS = '/Category:Science_packs'
URL_RESOURCES = '/Category:Resources'
URL_FLUIDS = '/Category:Fluids'


def main():
    resource_links = scrape_links(URL_RESOURCES)
    fluid_links = scrape_links(URL_FLUIDS)
    science_links = scrape_links(URL_SCIENCE_PACKS)
    for link in science_links:
        data = scrape_component_data(link)
        print(data['name'])
    component_links = [
        link for link in scrape_links(URL_INTERMEDIATE_PRODUCTS)
        if link not in resource_links
        and link not in fluid_links
        and link not in science_links
        and link != '/Space_science_pack'
    ]
    print("=========================")
    for link in component_links:
        data = scrape_component_data(link)
        print(data['name'])


def scrape_links(url):
    page = requests.get(DOMAIN + url)
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
    if not sidebar:
        return {
            'name': name,
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
