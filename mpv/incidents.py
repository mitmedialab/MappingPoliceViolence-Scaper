# DEPRECATED - USE INCIDENTSV4.PY, WHICH USES GOOGLE SHEETS APIv4

import requests, gspread, unicodecsv, logging, os
from oauth2client.client import GoogleCredentials

from mpv import basedir, config

log = logging.getLogger(__name__)

google_spreadsheet_url = config.get('spreadsheet','url')

def _get_spreadsheet_worksheet(google_sheets_url, google_worksheet_name):
    all_data = None
    log.info("Loading spreadsheet/"+google_worksheet_name+" data from url")
    credentials = GoogleCredentials.get_application_default()
    credentials = credentials.create_scoped(['https://spreadsheets.google.com/feeds'])
    gc = gspread.authorize(credentials)
    # Needed to share the document with the app-generated email in the credentials JSON file for discovery/access to work
    sh = gc.open_by_url(google_sheets_url)
    worksheet = sh.worksheet(google_worksheet_name)
    all_data = worksheet.get_all_values()
    return all_data

def _get_spreadsheet_data(google_sheets_url, google_worksheet_name):
    all_data = _get_spreadsheet_worksheet(google_sheets_url, google_worksheet_name)
    log.info("  loaded %d rows" % len(all_data))
    # write it to a local csv for inspection and storage
    outfile = open(os.path.join(basedir,'data','mpv-input-data.csv'), 'wb')
    outcsv = unicodecsv.writer(outfile,encoding='utf-8')
    for row in all_data:
        outcsv.writerow(row)
    outfile.close()
    # now return the list of all the data
    iter_data = iter(all_data)
    next(iter_data)         # Skip header row
    return iter_data

def get_query_adjustments():
    google_worksheet_name = config.get('spreadsheet','query_adjustement_worksheet')
    all_data = _get_spreadsheet_worksheet(google_spreadsheet_url, google_worksheet_name)
    log.info("  loaded %d rows" % len(all_data))
    all_data = iter(all_data)
    next(all_data)
    adjustment_map = {} # full name to keyword query terms
    for row in all_data:
        full_name = row[0]
        custom_query = row[4]
        if(len(custom_query)>0):
            adjustment_map[full_name] = custom_query
    log.info("  Found %d query keyword adjustments " % len(adjustment_map))
    return adjustment_map

def get_all():
    data = _get_spreadsheet_data(google_spreadsheet_url, config.get('spreadsheet','worksheet'))
    people = []
    for row in data:
        first_name = row[1]
        last_name = row[2]
        full_name = row[0]
        city = row[6]
        state = row[7]
        population = row[8]
        cause = row[9]
        sex = row[3]
        date_of_death = row[4]
        age = row[5]
        person =  {
            'full_name': full_name, 
            'first_name': first_name, 
            'last_name': last_name, 
            'sex': sex, 
            'date_of_death': date_of_death, 
            'age': age, 
            'city': city, 
            'state': state, 
            'cause': cause, 
            'population': population
        }
        people.append(person)
    return people
