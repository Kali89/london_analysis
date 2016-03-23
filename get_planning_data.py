import pandas as pd
from selenium import webdriver
import lxml.html
import mechanize
import cookielib

br = mechanize.Browser()

cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)

br.set_handle_equiv(True)
br.set_handle_gzip(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)

br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
postcodes = pd.read_csv('postcodes_of_interest.csv')
postcode_list = postcodes.postcode.unique()
all_data = []

for postcode in postcode_list:
    driver = webdriver.Firefox()
    driver.get('http://www.islington.gov.uk/services/planning/applications/comment/Pages/planning-search.aspx#header')
    driver.switch_to_frame(0)
    postcode_field = driver.find_element_by_name('txtPostCode')
    postcode_field.send_keys(postcode)
    submit_button = driver.find_element_by_id('csbtnSearch')
    submit_button.click()
    try:
        root = lxml.html.fromstring(driver.page_source)
        for row in root.xpath('.//table//tr'):
            cells = row.xpath('.//td/text()')
            cells = cells[2:]
            all_data.append(cells)

        all_pages = driver.find_elements_by_class_name('results_page_number')
        urls_to_visit = [entry.get_attribute('href') for entry in all_pages]
        for url in urls_to_visit:
            driver.get(url)
            root = lxml.html.fromstring(driver.page_source)
            for row in root.xpath('.//table//tr'):
                cells = row.xpath('.//td/text()')
                cells = cells[2:]
                all_data.append(cells)
    except:
        continue 

    driver.close()
