import mechanize
import cookielib
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

postcodes = pd.read_csv('angelpostcodes.csv')
postcode_list = postcodes.postcode.apply(lambda x: x.split()[0]).unique()

headers_list = [[('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')], [('User-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.93 Safari/537.36')], [('User-agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0')]]

br = mechanize.Browser()

cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)

br.set_handle_equiv(True)
br.set_handle_gzip(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)

br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

def extract_table_data(html):
    soup = BeautifulSoup(html)

    table = soup.find("table", attrs={"class":"data-table pfhidelastcolumn"})

    headings = [th.get_text().strip() for th in table.find('tr').find_all('th')]
    datasets = []

    for row in table.find_all('tr')[1:]:
        dataset = dict((heading, td.get_text().strip()) for heading, td in zip(headings, row.find_all('td')) if heading)
        datasets.append(dataset)
    return datasets, len(datasets)

all_datasets = []
for postcode in postcode_list:
    time.sleep(1)
    for descriptionCode in ['CP', 'CP1']:
        print(postcode)
        br.addheaders = random.choice(headers_list)
        br.open('http://www.2010.voa.gov.uk/rli/en/advanced')

        for entry in br.forms():
            formy = entry

        formy.set_value(postcode, 'postcode')
        formy.set_value([descriptionCode], 'descriptionCode')

        br.form = formy

        outy = br.submit()

        data = outy.get_data()

        page_number = 1
        try:
            data, size = extract_table_data(br.response().read())
            all_datasets.append(data)
        except:
            continue

        keep_going = True
        while keep_going:
            page_number += 1
            time.sleep(1)
            try:
                br.open('http://www.2010.voa.gov.uk/rli/en/advanced/searchResults/_params/page/%d' % page_number)
                data, size = extract_table_data(br.response().read())
                all_datasets.append(data)
            except:
                break
            if size < 10:
                keep_going = False

big_list = [item for sublist in all_datasets for item in sublist if type(item) != int]
dataframe = pd.DataFrame(big_list)
dataframe.columns = ['Address', 'Reference', 'Composite', 'Description', 'EffectiveDate', 'ListAlterationDate', 'PreviousProposals', 'RateableValue', 'SCatScode', 'SettleCode', 'Area', 'PoundPerMetre']
dataframe['RateableValue'] = dataframe.RateableValue.apply(lambda x: x.lstrip(u'\xa3').replace(',', ''))

dataframe.to_csv('valuationData.csv', index=False)
