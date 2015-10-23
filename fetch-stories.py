# `export GOOGLE_APPLICATION_CREDENTIALS=./GoogleSpreadsheetAccess-be765243bfb4.json`

import logging, os, sys, time, json, datetime, copy

import requests, gspread, unicodecsv
from oauth2client.client import GoogleCredentials

import mediacloud
from mpv import basedir, config, mc, db, cache

# set up logging
logging.basicConfig(filename=os.path.join(basedir,'fetcher.log'),level=logging.DEBUG)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
start_time = time.time()
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.DEBUG)
mc_logger = logging.getLogger('mediacloud')
mc_logger.setLevel(logging.DEBUG)

log.info("Using redis db %s as a cache" % config.get('cache','redis_db_number'))

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

def get_spreadsheet_data(google_sheets_url, google_worksheet_name):
    all_data = _get_spreadsheet_worksheet(google_sheets_url, google_worksheet_name)
    log.info("  loaded %d rows" % len(all_data))
    # write it to a local csv for inspection and storage
    outfile = open(os.path.join(basedir,'data','mpv_input_data.csv'), 'wb')
    outcsv = unicodecsv.writer(outfile,encoding='utf-8')
    for row in all_data:
        outcsv.writerow(row)
    outfile.close()
    # now return the list of all the data
    iter_data = iter(all_data)
    next(iter_data)         # Skip header row
    return iter_data

def get_query_adjustments(google_sheets_url, google_worksheet_name):
    all_data = _get_spreadsheet_worksheet(google_sheets_url, google_worksheet_name)
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

def zi_time(d):
    return datetime.datetime.combine(d, datetime.time.min).isoformat() + "Z"

def build_mpv_daterange(row):
    # from 5 days before the event, to 2 weeks afterwards
    date_object = datetime.datetime.strptime(row[4], '%Y-%m-%d')
    death_date = zi_time(date_object)
    before_date = date_object - datetime.timedelta(days=5)
    start_date = before_date.strftime('%Y-%m-%d')
    two_weeks_post_death = date_object + datetime.timedelta(days=14)
    date_range = '(publish_date:[{0} TO {1}])'.format(zi_time(before_date), zi_time(two_weeks_post_death))
    return date_range

#@cache
def fetch_all_stories(solr_query, solr_filter=''):
    log.info('Fetching stories for query {0}'.format(solr_query))
    start = 0
    offset = 500
    all_stories = []
    page = 0
    while True:
        log.debug("  querying for %s | %s" % (solr_query,solr_filter))
        stories = mc.storyList(solr_query=solr_query, solr_filter=solr_filter, last_processed_stories_id=start, rows=offset)
        log.info('  page %d' % page),
        all_stories.extend(stories)
        if len(stories) < 1:
            break
        start = max([s['processed_stories_id'] for s in stories])
        page = page + 1
    log.info('  Retrieved {0} stories for query {1}'.format(len(all_stories), solr_query))
    return all_stories

# grab the data from the Google spreadsheet
google_spreadsheet_url = config.get('spreadsheet','url')
data = get_spreadsheet_data(google_spreadsheet_url, config.get('spreadsheet','worksheet'))
custom_query_keywords = get_query_adjustments(google_spreadsheet_url, config.get('spreadsheet','query_adjustement_worksheet'))

# set up a csv to record all the story urls
story_url_csv_file = open(os.path.join(basedir,'data','mpv_story_urls.csv'), 'w')
fieldnames = ['full_name', 'first_name', 'last_name', 'sex', 'date_of_death', 'age', 'city', 'state', 'cause', 'story_date', 'population', 'stories_id', 'url' ]
story_url_csv = unicodecsv.DictWriter(story_url_csv_file, fieldnames = fieldnames, 
    extrasaction='ignore', encoding='utf-8')
story_url_csv.writeheader()

# set up a csv to record counts of all the stories per person
story_count_csv_file = open(os.path.join(basedir,'data','mpv_story_counts.csv'), 'w')
fieldnames = ['full_name', 'story_count' ]
story_count_csv = unicodecsv.DictWriter(story_count_csv_file, fieldnames = fieldnames, 
    extrasaction='ignore', encoding='utf-8')
story_count_csv.writeheader()

# iterate over all the queries grabbing stories and queing a req for bitly counts
queries = []
time_spent_querying = 0
time_spent_queueing = 0
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
    log.info("Working on %s" % full_name)

    #if data['full_name']!="Akai Gurley":
    #   continue

    query = ""
    name_key = data['first_name']+' '+data['last_name']
    if name_key in custom_query_keywords:
        log.info("  adjustment: %s -> %s" % (name_key,custom_query_keywords[name_key]))
        query = custom_query_keywords[name_key]
    else:
        query = '"{0}" AND "{1}"'.format(first_name, last_name)


    # a) limit query to correct date range only
    # query_filter = build_mpv_daterange(row)
    # b) also limit query to us media sources (msm, regional, partisan sets)
    query_filter = build_mpv_daterange(row) + " AND (tags_id_media:(8875027 2453107 129 8878292 8878293 8878294)) "
    # c) also limit query to non-spidered us media sources (msm, regional, partisan sets)
    # query_filter = build_mpv_daterange(row) + " AND (tags_id_media:(8875027 2453107 129 8878292 8878293 8878294)) " + " AND NOT (tags_id_stories:8875452) " 
    queries.append("("+query+" AND "+query_filter+")")

    query_start = time.time()
    stories = fetch_all_stories(query, query_filter)
    query_duration = float(time.time() - query_start)
    time_spent_querying = time_spent_querying + query_duration

    queue_start = time.time()
    duplicate_stories = 0 
    urls_already_done = []  # build a list of unique urls for de-duping

    log.info("  found %d stories" % len(stories))
    for story in stories:
        # figure out the base url so we can de-duplicate results from MC
        story['base_url'] = story['url']
        if '?' in story['base_url']:
            question_pos = story['base_url'].index('?')
            story['base_url'] = story['base_url'][:question_pos]        
        # now skip it if we have done it already
        if story['base_url'] in urls_already_done:   # skip duplicate urls that have different story_ids
            log.debug("    skipping story %s because we've alrady queued that url" % story['stories_id'])
            duplicate_stories = duplicate_stories + 1
            continue
        urls_already_done.append(story['base_url'])
        # skip if it is in the db already
        if db.storyExists(story['stories_id']):
            log.debug("    story in db already %s" % story['stories_id'])
            continue;
        # now go ahead and save it
        story_data = copy.deepcopy(data)
        story_data['story_date'] = story['publish_date']
        story_data['story_id'] = story['stories_id']
        story_data['stories_id'] = story['stories_id']
        story_url_csv.writerow(story_data)
        story_url_csv_file.flush()
        # now figure out how to save it
        existing_story = db.getStory(story['stories_id'])
        log.debug("    adding new story %s" % story['stories_id'])
        db.addStory(story,story_data)

    story_count_csv.writerow({'full_name':data['full_name'],'story_count':len(stories)-duplicate_stories})

    log.info("  Started with %d stories" % len(stories))
    log.info("    skipped %d stories that have duplicate urls" % duplicate_stories)
    queue_duration = float(time.time() - queue_start)
    time_spent_queueing = time_spent_queueing + queue_duration
    
log.info("Giant combined query is:")
log.info(" OR ".join(queries))

# log some stats about the run
duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
log.info("  took %d seconds to query" % time_spent_querying )
log.info("  took %d seconds to queue" % time_spent_queueing )

log.info("There are %d stories total in the db" % db.storyCount())
