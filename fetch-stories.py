# `export GOOGLE_APPLICATION_CREDENTIALS=./GoogleSpreadsheetAccess-be765243bfb4.json`

import logging, os, sys, time, json, datetime, copy

import requests, gspread, unicodecsv
from oauth2client.client import GoogleCredentials

import mediacloud, mpv.cache, mpv.tasks
from mpv import basedir, config, mc, db

# set up logging
logging.basicConfig(filename=os.path.join(basedir,'fetcher.log'),level=logging.INFO)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
start_time = time.time()
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.WARN)

# now grab the spreadsheet data
def get_spreadsheet_data(google_sheets_url, google_worksheet_name):
    cache_key = google_sheets_url+"_"+google_worksheet_name
    all_data = None
    if(mpv.cache.contains(cache_key)):
        log.info("Loading spreadsheet data from cache")
        all_data = json.loads(mpv.cache.get(cache_key))
    else:
        log.info("Loading spreadsheet data from url")
        credentials = GoogleCredentials.get_application_default()
        credentials = credentials.create_scoped(['https://spreadsheets.google.com/feeds'])
        gc = gspread.authorize(credentials)
        # Needed to share the document with the app-generated email in the credentials JSON file for discovery/access to work
        sh = gc.open_by_url(google_sheets_url)
        worksheet = sh.worksheet(google_worksheet_name)
        all_data = worksheet.get_all_values()
        mpv.cache.put(cache_key,json.dumps(all_data))
    # Skip header row
    log.info("  loaded %d rows" % len(all_data))
    iter_data = iter(all_data)
    next(iter_data)
    return iter_data
data = get_spreadsheet_data(config.get('spreadsheet','url'), config.get('spreadsheet','worksheet'))

def build_mpv_query(row):
    first_name = row[1]
    last_name = row[2]
    query = '"{0}" AND "{1}"'.format(first_name, last_name)
    return query

def zi_time(d):
    return datetime.datetime.combine(d, datetime.time.min).isoformat() + "Z"

def build_mpv_daterange(row):
    date_object = datetime.datetime.strptime(row[4], '%Y-%m-%d')
    death_date = zi_time(date_object)
    before_date = date_object - datetime.timedelta(days=5)
    start_date = before_date.strftime('%Y-%m-%d')
    two_weeks_post_death = date_object + datetime.timedelta(days=14)

    date_range = 'publish_date:[{0} TO {1}]'.format(zi_time(before_date), zi_time(two_weeks_post_death))
    return date_range

def fetch_all_stories(solr_query, solr_filter=''):
    log.info('Fetching stories for query {0}'.format(solr_query))
    cache_key = solr_query+"_"+solr_filter
    if mpv.cache.contains(cache_key):
        all_stories = json.loads(mpv.cache.get(cache_key))
        log.info('  Retrieved {0} stories for query {1} (from cache)'.format(len(all_stories), solr_query))
    else:
        start = 0
        offset = 500
        all_stories = []
        page = 0
        while True:
            stories = mc.storyList(solr_query=solr_query, solr_filter=solr_filter, last_processed_stories_id=start, rows=offset)
            log.info('  page %d' % page),
            all_stories.extend(stories)
            if len(stories) < 1:
                break
            start = max([s['processed_stories_id'] for s in stories])
            page = page + 1
        log.info('  Retrieved {0} stories for query {1}'.format(len(all_stories), solr_query))
        mpv.cache.put(cache_key,json.dumps(all_stories))
    return all_stories

# queue up requests to get all the stories for each row od data
story_url_csv_file = open('mpv_story_urls.csv', 'w')
fieldnames = ['full_name', 'first_name', 'last_name', 'sex', 'date_of_death', 'age', 'city', 'state', 'cause', 'story_date', 'population', 'stories_id', 'url' ]
story_url_csv = unicodecsv.DictWriter(story_url_csv_file, fieldnames = fieldnames, 
    extrasaction='ignore', encoding='utf-8')
story_url_csv.writeheader()

time_spent_querying = 0
time_spent_queueing = 0
for row in data:
    first_name = row[1]
    last_name = row[2]
    full_name = row[0].translate({',':None})
    city = row[6].translate({',':None})
    state = row[7]
    population = row[8].translate({',':None,'*':None})
    cause = row[9]
    sex = row[3]
    date_of_death = row[4]
    age = row[5]
    data =  {
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

    query = build_mpv_query(row)
    date_range = build_mpv_daterange(row)
    query_start = time.time()
    stories = fetch_all_stories(query, date_range)
    query_duration = float(time.time() - query_start)
    time_spent_querying = time_spent_querying + query_duration

    queue_start = time.time()
    queued_stories = 0
    skipped_stories = 0
    for story in stories:
        story_data = copy.deepcopy(data)
        story_data['story_date'] = story['publish_date']
        story_data['story_id'] = story['stories_id']
        story_data['stories_id'] = story['stories_id']
        story_data['url'] = story['url']
        story_url_csv.writerow(story_data)
        story_url_csv_file.flush()
        if not db.storyExists(story['stories_id']):
            # story_data['bitly_clicks'] will be filled in by celery task
            mpv.tasks.save_from_id.delay(story['url'],story_data)   # queue it up for geocoding
            queued_stories = queued_stories + 1
        else:
            log.debug("  skipping story %s - already in db" % story['stories_id'])
            skipped_stories = skipped_stories + 1
    log.info("  queued %d stories" % queued_stories)
    log.info("  skipped %d stories" % skipped_stories)
    queue_duration = float(time.time() - queue_start)
    time_spent_queueing = time_spent_queueing + queue_duration
    
# log some stats about the run
duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
log.info("  took %d seconds to query" % time_spent_querying )
log.info("  took %d seconds to queue" % time_spent_queueing )
