# -*- coding: utf-8 -*-
# basics stolen from https://developers.google.com/sheets/quickstart/python#step_3_set_up_the_sample

import httplib2
import os

from googleapiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

from mpv import basedir, config

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None
    
YEAR = int(config.get('spreadsheet','year')) # SET THIS TO THE YEAR OF DATA YOU WANT

# IDs for google spreadsheets of each year
SPREADSHEET_IDS = {2013: '1ArisyAjhUE1eeuA490-rPPI1nfft2cJIyDpaeOBqyj8',
                   2014: '1699_rxlNIK3KSNzqpoczw0ehiwTp4IKEaEP_dfWo6vM',
                   2015: '1HoG8jdioarEbxVI_IbuqRwQFCFqbUxzCHc6T2SymRUY',
                   2016: '19wsyttAqa4jbPnqmxQWbu79rwzp3eq_EHbzzsRiomTU'}
                   
# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/sheets.googleapis.com-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'mapping police violence'

def _get_credentials():
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
                                   'sheets.googleapis.com-python-quickstart.json')

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

def _setup():
    credentials = _get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
    service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)
    return service

def get_query_adjustments():
    '''returns a dictionary {name: adjusted_query}
    if query was not adjusted, adjusted_query is set to empty string'''
    
    service = _setup()
    spreadsheetId = SPREADSHEET_IDS[YEAR]

    if YEAR == 2016:
        rangeName = 'combined_clean'
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=rangeName, majorDimension = 'COLUMNS').execute()
        values = result.get('values', [])
        adjustments = ['('+s+')' for s in values[9] if s != '']
        namestoadjust = [n for i, n in enumerate(values[0]) if values[9][i] != '']
        return dict(zip(namestoadjust, adjustments))
    elif YEAR == 2015:
        rangeName = 'combined_clean'
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=rangeName, majorDimension = 'COLUMNS').execute()
        values = result.get('values', [])
        adjustments = ['('+s+')' for s in values[10] if s != '']
        namestoadjust = [n for i, n in enumerate(values[0]) if values[10][i] != '']
        return dict(zip(namestoadjust, adjustments))
    elif YEAR == 2014:
        #rangeName = 'Story Counts & Query Adjustments'
        rangeName = 'clean'
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=rangeName, majorDimension = 'COLUMNS').execute()
        values = result.get('values', [])
        #adjustments = ['('+s+')' for s in values[4] if s != '']
        #namestoadjust = [n for i, n in enumerate(values[0]) if values[4][i] != '']
        adjustments = ['('+s+')' for s in values[9] if s != '']
        namestoadjust = [n for i, n in enumerate(values[0]) if values[9][i] != '']
        return dict(zip(namestoadjust, adjustments))
    elif YEAR == 2013:
        rangeName = 'clean'
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=rangeName, majorDimension = 'COLUMNS').execute()
        values = result.get('values', [])
        adjustments = ['('+s+')' for s in values[9] if s != '']
        namestoadjust = [n for i, n in enumerate(values[0]) if values[9][i] != '']
        return dict(zip(namestoadjust, adjustments))
    else:
        print('NO DATA FOR YEAR ', YEAR)
        return {}

def get_all():
    '''get metadata for each person, as a list of dictionaries where each dictionary is one person 
    e.g. [{name:value, data:value}, {name: value, data: value}, {name: value, data: value}]'''
    
    service = _setup()
    spreadsheetId = SPREADSHEET_IDS[YEAR]
    
    if YEAR == 2016:
        rangeName = 'combined_clean'
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=rangeName, majorDimension = 'ROWS').execute()
        values = result.get('values', [])[1:]
        people = [{'full_name': row[0],
                   'date_of_death': row[2]} 
                   for row in values]
        return people
    elif YEAR == 2015:
        rangeName = 'combined_clean'
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=rangeName, majorDimension = 'ROWS').execute()
        values = result.get('values', [])[1:]
        people = [{'full_name': row[0],
                   'date_of_death': row[2]} 
                   for row in values]
        return people    
    elif YEAR == 2014:
        #rangeName = 'Death Details'
        rangeName = 'clean'
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=rangeName, majorDimension = 'ROWS').execute()
        values = result.get('values', [])[1:]
        #people = [{'full_name': row[0],
        #           'date_of_death': row[4],
        #           'first_name': row[1],
        #           'last_name': row[2]}
        #           for row in values]
        people = [{'full_name': row[0],
                   'date_of_death': row[2]} 
                   for row in values]
        return people
    elif YEAR == 2013:
        rangeName = 'clean'
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheetId, range=rangeName, majorDimension = 'ROWS').execute()
        values = result.get('values', [])[1:]
        people = [{'full_name': row[0],
                   'date_of_death': row[2]} 
                   for row in values]
        return people
    else:
        print('NO DATA FOR YEAR ', YEAR)
        return []