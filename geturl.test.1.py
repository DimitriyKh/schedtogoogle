#!/usr/bin/python3


import urllib.request
import urllib.parse
import re


import configparser


#set config file location
configfile="./.conf"


Config = configparser.ConfigParser()

Config.read(configfile)

#.conf MUST be as follows
#[URLs to parse] 
#url=
#url2=
#[login info]
#user=
#password=
#[Google credentials]
#google_account=
#google_password=

#Config['URLs to parse']['url']
#Config['URLs to parse']['url2']
#Config['login info']['user']
#Config['login info']['password']
#Config['Google credentials']['google_account']
#Config['Google credentials']['google_password']

url=Config['URLs to parse']['url']  
url2=Config['URLs to parse']['url2']  
user=Config['login info']['user']
password=Config['login info']['password'] 
google_account=Config['Google credentials']['google_account']
google_password=Config['Google credentials']['google_password']


lead_shift_duration="12:15"
notlead_shift_duration="12:00"
day_shift_start="08:45"
night_shift_start="20:45"

shifts=[]

user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
headers = {'User-Agent': user_agent}

print(url)
print(type(url))


password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, url, user, password)
handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
opener = urllib.request.build_opener(handler)
opener.open(url)
urllib.request.install_opener(opener)

req = urllib.request.Request(url, data=None, headers=headers)

with urllib.request.urlopen(req) as response:
  html = response.read().decode('utf-8')

# Этот класс делает 100% что мне надо, спасибо автору:
# https://github.com/schmijos/html-table-parser-python3/blob/master/html_table_parser/parser.py
# -----------------------------------------------------------------------------
# Name:        html_table_parser
# Purpose:     Simple class for parsing an (x)html string to extract tables.
#              Written in python3
#
# Author:      Josua Schmid
#
# Created:     05.03.2014
# Copyright:   (c) Josua Schmid 2014
# Licence:     AGPLv3

from html.parser import HTMLParser

class HTMLTableParser(HTMLParser):
    """ This class serves as a html table parser. It is able to parse multiple
    tables which you feed in. You can access the result per .tables field.
    """
    def __init__(
        self,
        decode_html_entities=False,
        data_separator=' ',
    ):

        HTMLParser.__init__(self)

        self._parse_html_entities = decode_html_entities
        self._data_separator = data_separator

        self._in_td = False
        self._in_th = False
        self._current_table = []
        self._current_row = []
        self._current_cell = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        """ We need to remember the opening point for the content of interest.
        The other tags (<table>, <tr>) are only handled at the closing point.
        """
        if tag == 'td':
            self._in_td = True
        if tag == 'th':
            self._in_th = True

    def handle_data(self, data):
        """ This is where we save content to a cell """
        if self._in_td or self._in_th:
            self._current_cell.append(data.strip())

    def handle_charref(self, name):
        """ Handle HTML encoded characters """

        if self._parse_html_entities:
            self.handle_data(self.unescape('&#{};'.format(name)))

    def handle_endtag(self, tag):
        """ Here we exit the tags. If the closing tag is </tr>, we know that we
        can save our currently parsed cells to the current table as a row and
        prepare for a new row. If the closing tag is </table>, we save the
        current table and prepare for a new one.
        """
        if tag == 'td':
            self._in_td = False
        elif tag == 'th':
            self._in_th = False

        if tag in ['td', 'th']:
            final_cell = self._data_separator.join(self._current_cell).strip()
            self._current_row.append(final_cell)
            self._current_cell = []
        elif tag == 'tr':
            self._current_table.append(self._current_row)
            self._current_row = []
        elif tag == 'table':
            self.tables.append(self._current_table)
            self._current_table = []
 
# -----------------------------------------------------------------------------

# создаём объект и помощью крутого класса и парсим всё в удобной табличку (2D list)
p = HTMLTableParser()
p.feed(html)
table = p.tables

# Я использую лябда функцию чтобы пройти по лямбда функции пока она перебирает 2D список. 
#user's column in table
col = [y for y in [x for x in table][0] if "09:00" in y][0].index(user.upper())

#повортим для закрепления
#get column No for shiftead
s = [s for s in [x for x in table][0] if "Day" in s][0]
leads = [i for i,x in enumerate(s) if x == "12.25"]

day = re.compile('(?:0?[7-9]|1[0-9]):[0-5][0-9]')
night = re.compile('2[0-3]:[0-5][0-9]')

#А вот тут я уже устал хитрить с lambda и написал всё "в лоб"
for row in table[0]:
 if user.upper() in row:
  if  day.match(row[col]):
    if user.upper() in row[leads[0]]:
      shifts.append([row[0],'day','lead'])
    else:
      shifts.append([row[0],'day','notlead'])
  elif night.match(row[col]):
    if user.upper() in row[leads[1]]:
      shifts.append([row[0],'night','lead']) 
    else:
      shifts.append([row[0],'night','notlead'])

print(shifts)

## Я так так и не знаю какой месяц в расписании... забыл :)
