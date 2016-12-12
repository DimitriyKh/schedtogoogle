#!/usr/bin/python3


import urllib.request
import urllib.parse
import re


import configparser


#set config file location
#configfile="./.conf"
configfile="../.conf.hideit"

Config = configparser.ConfigParser()

Config.read(configfile)

#ленивый парсинг конфига
url=Config['URLs to parse']['url']  
url2=Config['URLs to parse']['url2']  
user=Config['login info']['user']
password=Config['login info']['password'] 

calendarID=Config['Google side']['calendarID']


lead_shift_duration="12:15"
notlead_shift_duration="12:00"
day_shift_start="08:45"
night_shift_start="20:45"

shifts=[]

## переменные выше этой черты, а всё ниже - константами будет

user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
headers = {'User-Agent': user_agent}

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

# создаём объект и помощью крутого класса и парсим всё в удобную табличку (2D list)
p = HTMLTableParser()
p.feed(html)
table = p.tables

print(table)

# Я использую лямбда функцию чтобы пройти по лямбда функции пока она перебирает 2D список. 
#user's column in table
col = [y for y in [x for x in table][0] if "09:00" in y][0].index(user.upper())

#повортим для закрепления
#get column No for shiftead
s = [s for s in [x for x in table][0] if "Day" in s][0]
leads = [i for i,x in enumerate(s) if x == "12.25"]

day = re.compile('(?:0?[7-9]|1[0-9]):[0-5][0-9]')
night = re.compile('2[0-3]:[0-5][0-9]')

#А вот тут я уже устал хитрить с lambda и написал всё "в лоб"
#for row in table[0]:
# if user.upper() in row:
#  if  day.match(row[col]):
#    if user.upper() in row[leads[0]]:
#      shifts.append([row[0],'day','lead'])
#    else:
#      shifts.append([row[0],'day','notlead'])
#  elif night.match(row[col]):
#    if user.upper() in row[leads[1]]:
#      shifts.append([row[0],'night','lead']) 
#    else:
#      shifts.append([row[0],'night','notlead'])
#print(shifts)

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

#overkill но просто было интересно 
month,year = str(table[0][1][8]).split()
import calendar
month=dict((v,k) for k,v in enumerate(calendar.month_name))[month]
#print("month is:",month,", year is:",year)


print("------------")


#here starts google calendar part
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = '.client_secret.json'
APPLICATION_NAME = 'Schedule parser into  Google Calendar events (API Python version)'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

## from quickstart guide 
def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    eventsResult = service.events().list(
        calendarId='primary', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])


#if __name__ == '__main__':
#    main()
#
#print("------------")


def updshcedule():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    ## format an event
    event = {
      'summary':'Next Shift',
      'description':'this a shift',
      "start": {
        "timeZone": "Europe/Kiev",
        "dateTime": "2016-12-12T08:45:00+02:00", # RFC3339 formatted, time zone offset is required unless a time zone is explicitly specified in timeZone. example '2008-09-08T22:47:31-07:00'
      },
      "end": {
        "timeZone": "Europe/Kiev",
        "dateTime": "2016-12-12T21:00:00+02:00",
      },
      'reminders':{
        'useDefault':False,
        'overrides': [
          {'method': 'email', 'minutes': 2*60},
          {'method': 'popup', 'minutes': 35},
        ],
      },
    }

    ## submit the event
    eventResult = service.events().insert(calendarId=calendarID, body=event).execute()

    #получить список календарей
    #page_token = None
    #while True:
    #  calendar_list = service.calendarList().list(pageToken=page_token).execute()
    #  for calendar_list_entry in calendar_list['items']:
    #    print(calendar_list_entry)
    #    #print(calendar_list_entry['summary'])
    #  page_token = calendar_list.get('nextPageToken')
    #  if not page_token:
    #    break
    #


    #calendar_list_entry = service.calendarList().get(calendarId='Work').execute()

    #print(calendar_list_entry['summary'])

    print(eventResult)

#updshcedule()
