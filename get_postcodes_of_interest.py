from bs4 import BeautifulSoup
import pandas as pd
import requests
from xml.etree import ElementTree

RADIUS = 1
POSTCODE = 'EC1V 1NE'

def get_lat_and_long_of_postcode(postcode):
    response = requests.get('http://www.uk-postcodes.com/postcode/%s.json' % postcode.replace(' ',''))
    geo_info = response.json()['geo']
    return {'lat' : geo_info['lat'], 'long' : geo_info['lng']}

lat_and_long = get_lat_and_long_of_postcode(POSTCODE)

output = requests.get('https://www.freemaptools.com/ajax/get-all-full-postcodes-inside.php?radius=%.2f&lat=%.9f&lng=%.9f&rn=3242' % (RADIUS, lat_and_long['lat'], lat_and_long['long']))

e = ElementTree.fromstring(output.content)

all_codes = pd.DataFrame([{'postcode' : entry.get('outcode'), 'distance' : entry.get('dist')} for entry in e.findall('./marker')])

all_codes.to_csv('postcodes_of_interest.csv', index=False)
