# `export GOOGLE_APPLICATION_CREDENTIALS=./GoogleSpreadsheetAccess-be765243bfb4.json`

import logging, os, sys, time, json, datetime, copy

import requests, gspread, unicodecsv
from oauth2client.client import GoogleCredentials

import mediacloud, mpv.cache
from mpv import basedir, config, mc, db

# set up logging
logging.basicConfig(filename=os.path.join(basedir,'fetcher.log'),level=logging.DEBUG)
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

def zi_time(d):
    return datetime.datetime.combine(d, datetime.time.min).isoformat() + "Z"

def build_mpv_daterange(row):
    # from 5 days before the event, to 2 weeks afterwards
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

# grab the data from the Google spreadsheet
data = get_spreadsheet_data(config.get('spreadsheet','url'), config.get('spreadsheet','worksheet'))

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

    if data['full_name']!="Akai Gurley":
       continue

    query = '"{0}" AND "{1}"'.format(first_name, last_name)
    date_range = build_mpv_daterange(row)
    query_start = time.time()
    stories = fetch_all_stories(query, date_range)
    query_duration = float(time.time() - query_start)
    time_spent_querying = time_spent_querying + query_duration

    queue_start = time.time()
    stories_to_queue = 0
    stories_with_bitly_data = 0   
    duplicate_stories = 0 
    urls_already_done = []  # build a list of unique urls for de-duping

    for story in stories:
        if story['url'] in urls_already_done:   # skip duplicate urls that have different story_ids
            #log.warn("  skipping story %s because we've alrady queued that url" % story['stories_id'])
            duplicate_stories = duplicate_stories + 1
            continue
        urls_already_done.append(story['url'])
        story_data = copy.deepcopy(data)
        story_data['story_date'] = story['publish_date']
        story_data['story_id'] = story['stories_id']
        story_data['stories_id'] = story['stories_id']
        story_url_csv.writerow(story_data)
        story_url_csv_file.flush()
        needs_bitly_data = False
        existing_story = db.getStory(story['stories_id'])
        if existing_story is None:
            needs_bitly_data = True
            db.addStory(story,story_data)
            existing_story = db.getStory(story['stories_id'])
        else:
            if 'bitly_clicks' in existing_story:
                needs_bitly_data = False
                stories_with_bitly_data = stories_with_bitly_data + 1
            else:
                needs_bitly_data = True
        if needs_bitly_data:
            bitly_cache_key = str(story_data['story_id'])+"_bitly_stats"
            if mpv.cache.contains(bitly_cache_key):
                bitly_stats = json.loads(mpv.cache.get(bitly_cache_key))
                total_click_count = bitly_stats['total_click_count']
                log.debug("  updating existing story")
                new_data = {'bitly_clicks': total_click_count }
                db._db.stories.update({'_id':existing_story['_id']}, {"$set": new_data})
                #db.updateStory(story)
                log.info("  Story %s - %d clicks (from cache)" % (story_data['story_id'], total_click_count))
            else:
                stories_to_queue = stories_to_queue + 1
        else:
            log.debug("  skipping story %s - bitly data already in db" % story['stories_id'])

    story_count_csv.writerow({'full_name':data['full_name'],'story_count':len(stories)})

    log.info("  %d stories need bitly counts" % stories_to_queue)
    log.info("  skipped %d stories that alreay have bitly counts in db" % stories_with_bitly_data)
    log.info("  skipped %d stories that have duplicate urls" % duplicate_stories)
    queue_duration = float(time.time() - queue_start)
    time_spent_queueing = time_spent_queueing + queue_duration
    
# log some stats about the run
duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
log.info("  took %d seconds to query" % time_spent_querying )
log.info("  took %d seconds to queue" % time_spent_queueing )

stories_with_data = db._db.stories.find( { 'bitly_clicks': {'$exists': True} }).count();
stories_needing_data = db._db.stories.find( { 'bitly_clicks': {'$exists': False} }).count();

log.info("There are %d stories total in the db" % db.storyCount())
log.info("  %d stories with data" % stories_with_data)
log.info("  %d stories needing data" % stories_needing_data)

