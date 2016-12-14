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

timeZone="Europe/Kiev"

#lead_shift_duration="12:15:00"
#notlead_shift_duration="12:00:00"
day_lead_shift_start="08:45:00"
night_lead_shift_start="20:45:00"
day_shift_start="09:00:00"
night_shift_start="21:00:00"
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

# создаём объект и c помощью крутого класса и парсим всё в удобную табличку (2D list)
p = HTMLTableParser()
p.feed(html)
table = p.tables

print(table)

print("------------")

# Я использую лямбда функцию чтобы пройти по лямбда функции пока она перебирает 2D список. 
#user's column in table
col = [y for y in [x for x in table][0] if "09:00" in y][0].index(user.upper())

#повторим для закрепления
s = [s for s in [x for x in table][0] if "Day" in s][0]
#get column No for shiftead
leads = [i for i,x in enumerate(s) if x == "12.25" or x == "12,25" ]


day = re.compile('(?:0?[7-9]|1[0-9]):[0-5][0-9]')
night = re.compile('2[0-3]:[0-5][0-9]')

month,year = str(table[0][1][8]).split()

Months_En = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6, 'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}
#это какой-то треш, каждый раз в расписании новые сюрпризы
Months_Ru = {'Январь': 1, 'Февраль': 2, 'Март': 3, 'Апрель': 4, 'Май': 5, 'Июнь': 6, 'Июль': 7, 'Август': 8, 'Сентябрь': 9, 'Октябрь': 10, 'Ноябрь': 11, 'Декабрь': 12}

try:
  month=Months_En[month]
except:
  try:
    month=Months_Ru[month]
  except:
    raise
    
#А было б всё на англ, сделал бы так. Overkill, но красиво.
#import calendar
#month=dict((v,k) for k,v in enumerate(calendar.month_name))[month]

month,year = str(month),str(year)

#Ога, иногда есть день-другой на следующий месяц, приходится и это проверять
lastday='0'

for row in table[0]:
  if user.upper() in row:
    if  day.match(row[col]):
      if int(lastday) < int(row[0]):
        if user.upper() in row[leads[0]]:
          shifts.append([year+"-"+month+"-"+re.sub("(?<!\d)(\d)(?!\d)", '0\\1', row[0])+"T"+str(day_lead_shift_start), year+"-"+month+"-"+re.sub("(?<!\d)(\d)(?!\d)", '0\\1', row[0])+"T"+str(night_shift_start)])
          lastday=row[0]
        else:
          shifts.append([year+"-"+month+"-"+re.sub("(?<!\d)(\d)(?!\d)", '0\\1', row[0])+"T"+day_shift_start, year+"-"+month+"-"+re.sub("(?<!\d)(\d)(?!\d)", '0\\1', row[0])+"T"+night_shift_start])
          lastday=row[0]
    elif night.match(row[col]):
      if int(lastday) < int(row[0]):
        if user.upper() in row[leads[1]]:
          shifts.append([year+"-"+month+"-"+re.sub("(?<!\d)(\d)(?!\d)", '0\\1', row[0])+"T"+night_lead_shift_start, year+"-"+month+"-"+re.sub("(?<!\d)(\d)(?!\d)", '0\\1', str(int(row[0])+1))+"T"+day_shift_start])
          lastday=row[0]
        else:
          shifts.append([year+"-"+month+"-"+re.sub("(?<!\d)(\d)(?!\d)", '0\\1', row[0])+"T"+night_shift_start, year+"-"+month+"-"+re.sub("(?<!\d)(\d)(?!\d)", '0\\1', str(int(row[0])+1))+"T"+day_shift_start])
          lastday=row[0]

print(shifts)

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

def getcurrentcalendar(calendarID):
    """Shows basic usage of the Google Calendar API.
    Creates a Google Calendar API service object and outputs a list of 
    events for given calendar id
    """
    currentcalendar=[]
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    curmonth = '{:%Y-%m-01T00:00:00}Z'.format(datetime.datetime.now())
    nextmonth = '{:%Y-%m-01T00:00:00}Z'.format(datetime.datetime.now()+datetime.timedelta(365/12))

    eventsResult = service.events().list(
        calendarId=calendarID, timeMin=curmonth, timeMax=nextmonth, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start, end = event['start'].get('dateTime')[:-6],  event['end'].get('dateTime')[:-6]
        #start, end = event['start'].get('dateTime'),  event['end'].get('dateTime')
        currentcalendar.append([start, end])

    print(currentcalendar)


getcurrentcalendar(calendarID)

def updshcedule(start,end):
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    ## format an event
    ## dateTime is RFC3339 formatted, time zone offset is required unless a time zone is explicitly specified in timeZone. example '2008-09-08T22:47:31-07:00'
    event = {
      'summary':'Next Shift',
      'description':'this is a shift',
      "start": {
        "timeZone": "Europe/Kiev",
        "dateTime": start,
      },
      "end": {
        "timeZone": "Europe/Kiev",
        "dateTime": end,
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

    print(eventResult)

#for start,end  in shifts:
#  updshcedule(start,end)
