# Story Count Queries and Bitly Stats Aggregator for MappingPoliceViolence
# `export GOOGLE_APPLICATION_CREDENTIALS=./GoogleSpreadsheetAccess-be765243bfb4.json`

import gspread
import time
import os
import sys
import logging
import datetime
import mediacloud
import ConfigParser
from datetime import date
from oauth2client.client import GoogleCredentials
import grequests
import requests
import unicodecsv, urllib
import cache, json

# base directory for relative paths
basedir = os.path.dirname(os.path.abspath(__file__))

def zi_time(d):
	return datetime.datetime.combine(d, datetime.time.min).isoformat() + "Z"

def fetch_all_stories(solr_query, solr_filter=''):
    logging.info('Fetching stories for query {0}'.format(solr_query))
    cache_key = cache.md5_key(solr_query+"_"+solr_filter)
    if cache.contains(cache_key):
        all_stories = json.loads(cache.get(cache_key))
        logging.info('  Retrieved {0} stories for query {1} (from cache)'.format(len(all_stories), solr_query))
    else:
        start = 0
        offset = 500
        all_stories = []
        start_time = time.time()
        while True:
            stories = mc.storyList(solr_query=solr_query, solr_filter=solr_filter, last_processed_stories_id=start, rows=offset)
            logging.info('.'),
            sys.stdout.flush()
            all_stories.extend(stories)
            if len(stories) < 1:
                break
            start = max([s['processed_stories_id'] for s in stories])
        logging.info('  Retrieved {0} stories for query {1}'.format(len(all_stories), solr_query))
        cache.put(cache_key,json.dumps(all_stories))
    return all_stories

def get_spreadsheet_data(google_sheets_url, google_worksheet_name):
    credentials = GoogleCredentials.get_application_default()
    credentials = credentials.create_scoped(['https://spreadsheets.google.com/feeds'])
    gc = gspread.authorize(credentials)
    # Needed to share the document with the app-generated email in the credentials JSON file for discovery/access to work
    sh = gc.open_by_url(google_sheets_url)
    worksheet = sh.worksheet(google_worksheet_name)
    all_data = worksheet.get_all_values()
    
    # Skip header row
    iter_data = iter(all_data)
    next(iter_data)

    return iter_data

def get_mc():
    config = ConfigParser.ConfigParser()
    config.read(os.path.join(basedir, 'app.config'))
    api_key = config.get('mediacloud', 'key')
    logging.info('MediaCloud API Initializing...')
    mc = mediacloud.api.AdminMediaCloud(api_key)
    logging.info('  MediaCloud API Initialized.')
    return mc

def build_mpv_query(row):
    first_name = row[1]
    last_name = row[2]
    query = '"{0}" AND "{1}"'.format(first_name, last_name)
    return query

def build_mpv_daterange(row):
    date_object = datetime.datetime.strptime(row[4], '%Y-%m-%d')
    death_date = zi_time(date_object)
    before_date = date_object - datetime.timedelta(days=5)
    start_date = before_date.strftime('%Y-%m-%d')
    today = datetime.date.today()
    end_date = today.strftime('%Y-%m-%d')
    two_weeks_post_death = date_object + datetime.timedelta(days=14)

    date_range = 'publish_date:[{0} TO {1}]'.format(zi_time(before_date), zi_time(two_weeks_post_death))
    return date_range

def get_bitly_clicks(url, just_the_url=False):
    now = datetime.datetime.now()
    max_range = datetime.timedelta(days=1000)
    start_ts = (now - max_range).strftime('%s')
    end_ts = date.today().strftime('%s')
    total_click_count = None
    try:
        if just_the_url:
            return mc.storyBitlyClicks(start_ts, end_ts, url=url.encode('utf8'), return_url_only=True)
        stats = mc.storyBitlyClicks(start_ts, end_ts, url=url)
        total_click_count = stats['total_click_count']
    except mediacloud.error.MCException as mce:
        if mce.status_code==404:
            logging.info("404 - No clicks in bitly")
            total_click_count = 0
        elif mce.status_code==429:
            logging.error("429 - Hit the bitly API limit!")
            total_click_count = -2
        elif mce.status_code==500:
            logging.error("500 - MC had an error!")
            total_click_count = -3
        else:
            logging.error("%d unknown error!" % mce.status_code)
            total_click_count = -4
    logging.info("  - %d clicks" % total_click_count)
    return total_click_count

def find_in_list_by_sid(urls,search_url):
    search_sid = search_url.split("=")[-1]
    idx = 0
    for u in urls:
        sid = u.split("=")[-1]
        if sid == search_sid:
            return idx
        idx = idx+1
    return None

def __main__():
    
    data = get_spreadsheet_data('https://docs.google.com/spreadsheets/d/1699_rxlNIK3KSNzqpoczw0ehiwTp4IKEaEP_dfWo6vM/edit?pli=1#gid=863965989', 'Death Details')
    row_idx = 0
    with open('mpv_story_data_{0}.csv'.format(time.time() * 1000), 'wb') as csv_file:
        csv_writer = unicodecsv.writer(csv_file, encoding='utf-8')
        csv_writer.writerow( ['full_name', 'first_name', 'last_name', 'sex', 'date_of_death', 'age', 'city', 'state', 'cause', 'story_date', 'bitly_clicks', 'population', 'story_id' ])
        csv_file.flush()
        count = 0
        for row in data:
            logging.info("Row %d" % row_idx)
            count = count + 1
            first_name = row[1]
            last_name = row[2]
            full_name = row[0].translate(None, ',')
            city = row[6].translate(None, ',')
            state = row[7]
            population = row[8].translate(None, ',*')
            cause = row[9]
            sex = row[3]
            date_of_death = row[4]
            age = row[5]

            query = build_mpv_query(row)
            date_range = build_mpv_daterange(row)
            stories = fetch_all_stories(query, date_range)

            sid2results = {}
            idx = 0
            for s in stories:
                url = get_bitly_clicks(s['url'], True) + "&sid=" + str(s['stories_id']) # tack on id for lookup later by url from http response obj
                d = {
                    'story_date': s['publish_date'],
                    'story_id': s['stories_id'],
                    'mc_bitly_query_url': url,
                    'bitly_results_cache_key': 'bitly'+str(s['stories_id'])
                }
                if(cache.contains(d['bitly_results_cache_key'])):
                    d['bitly_clicks'] = int(cache.get(d['bitly_results_cache_key']))
                    logging.debug("  loaded bitly results for %s from local cache" % d['story_id'])
                sid2results[int(d['story_id'])] = d
                idx = idx + 1

            # now run through all the urls for stories asking for click counts in parallel
            urls = [v['mc_bitly_query_url'] for k,v in sid2results.iteritems() if 'bitly_clicks' not in v]
            http_requests = (grequests.get(u) for u in urls)
            urls = [req.url for req in http_requests]
            while len(urls)>0:
                url_batch = urls[-10:]  # parallel fetch results for N stories at a time
                try:
                    rs = (grequests.get(u) for u in url_batch)
                    responses = grequests.map(rs)
                    for r in responses:
                        if r==None:
                            logging.error("got a None response for one of the urls...")
                            continue
                        sid = int(r.url.split("=")[-1])
                        if sid not in sid2results:
                            logging.error("Couldn't find story data in sid2results for:")
                            logging.error("  %s" % r.url.split("=")[-1])
                            logging.error(json.dumps(sid2results.keys()))
                            for k in sid2results.keys():
                                logging.error("  %s==%s = %s" % (sid,k,sid==k))
                            sys.exit()
                        d = sid2results[sid]
                        click_count = -4
                        retry = False
                        logging.debug("  %d on story on %s" % (r.status_code,d['story_id']))
                        if r.status_code == 200:
                            click_count = r.json()['total_click_count']
                        elif r.status_code == 404:
                            click_count = 0     # url not in bitly db
                        elif r.status_code == 429:
                            click_count = -2    # we hit the api limit
                            logging.error("We hit the bitly API limit, bailing because nothing after this will work!")
                            sys.exit()
                        elif r.status_code == 500:
                            # MC had some kind of error, so try it again
                            retry = True
                            time.sleep(1)
                        if not retry:
                            cache.put(d['bitly_results_cache_key'],str(click_count))
                            logging.debug("  added %s results to local cache" % d['story_id'])
                            d['bitly_clicks'] = click_count
                            idx_to_remove = find_in_list_by_sid(urls,r.url)
                            if idx_to_remove==None:
                                logging.error("Couldn't find a url in lookup:")
                                logging.error("  %s" % r.request.url)
                                logging.error(json.dumps(urls))
                                sys.exit()
                            else:
                                del urls[idx_to_remove]
                except requests.exceptions.SSLError:
                    logger.warn("parallel request failed with SSLError... trying again in 1 second")
                    time.sleep(1)
            # now for each story write a row of the results
            for s in sid2results.values():
                csv_writer.writerow( [
                    full_name, first_name, last_name, sex, date_of_death, age, city, 
                    state, cause, s['story_date'], s['bitly_clicks'], population, s['story_id'] 
                ] )
            csv_file.flush()
            row_idx = row_idx + 1

if __name__ == "__main__":
    log_path = os.path.join(basedir, 'mpv_generate_story_data.log')
    print('Logging to '+log_path)
    logging.basicConfig(filename=log_path, level=logging.DEBUG)
    logging.info('------------------------------------------------------------------------------')
    logging.info('Starting!')
    mc = get_mc()
    __main__()

