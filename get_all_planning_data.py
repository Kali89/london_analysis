import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import lxml.html
import mechanize
import cookielib

all_data = []

with open('ward_values.txt', 'rb') as f:
    ward_values = [entry.strip() for entry in f.readlines() if entry.strip()[0] != '#']

def get_data_from_html(html):
    data = []
    root = lxml.html.fromstring(html)
    for row in root.xpath('.//table//tr'):
        cells = row.xpath('.//td/text()')
        cells = cells[2:]
        if cells:
            data.append(cells)
    return data

def get_urls_of_next_pages(driver):
    all_pages = driver.find_elements_by_class_name('results_page_number')
    urls_to_visit = [entry.get_attribute('href') for entry in all_pages]
    return urls_to_visit

for ward in ward_values:
    driver = webdriver.Firefox()
    driver.get('http://www.islington.gov.uk/services/planning/applications/comment/Pages/planning-search.aspx#header')
    driver.switch_to_frame(0)
    select = Select(driver.find_element_by_name('cboWardCode'))
    select.select_by_visible_text(ward)
    submit_button = driver.find_element_by_id('csbtnSearch')
    submit_button.click()
    all_data = all_data + get_data_from_html(driver.page_source)
    urls_to_visit = get_urls_of_next_pages(driver)
    urls_visited = []
    while urls_to_visit:
        url = urls_to_visit.pop(0)
        driver.get(url)
        root = lxml.html.fromstring(driver.page_source)
        for row in root.xpath('.//table//tr'):
            cells = row.xpath('.//td/text()')
            cells = cells[2:]
            all_data.append(cells)
        urls_visited.append(url)
        new_pages_to_visit = get_urls_of_next_pages(driver)
        temp_urls_to_visit = set(new_pages_to_visit) - set(urls_visited) - set(urls_to_visit)
        temp_urls_to_visit = [url for url in temp_urls_to_visit if url.split('&')[-1] != 'p=0']
        urls_to_visit = urls_to_visit + temp_urls_to_visit
    driver.close()

df = pd.DataFrame(all_data)
df.columns = ['Address', 'Description', 'Status', 'Date', 'Outcome']
df['Description'] = df.Description.apply(lambda x: x.strip().encode('utf-8', 'ignore') if x else None)
df['Address'] = df.Address.apply(lambda x: x.strip().encode('utf-8', 'ignore') if x else None)
df.to_csv('other_planning_data.csv', index=False)
