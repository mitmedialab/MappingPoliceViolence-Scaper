import logging, os, sys, time, json, datetime, copy
import requests, gspread, unicodecsv
import mediacloud
from mpv import basedir, config, mc, mca, cache, incidentsv4, dest_dir
from mpv.util import build_mpv_daterange

CONTROVERSY_ID = config.get('mediacloud','controversy_id')

# set up logging
logging.basicConfig(filename=os.path.join(basedir,'logs',
    config.get('spreadsheet','year')+'list-all-stories.log'),level=logging.DEBUG)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
start_time = time.time()
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.INFO)
mc_logger = logging.getLogger('mediacloud')
mc_logger.setLevel(logging.INFO)

log.info("Using redis db %s as a cache" % config.get('cache','redis_db_number'))

log.info("Working from controversy %s" % CONTROVERSY_ID)

results = mc.storyCount("{~ topic:"+CONTROVERSY_ID+"}")
log.info("  %s total stories" % results)

data = incidentsv4.get_all()
custom_query_keywords = incidentsv4.get_query_adjustments()

@cache
def fetch_all_stories(solr_query, solr_filter=''):
    log.info('Fetching stories for query {0}'.format(solr_query))
    start = 0
    offset = 500
    all_stories = []
    page = 0
    while True:
        log.debug("  querying for %s | %s" % (solr_query,solr_filter))
        stories = mc.storyList(solr_query=solr_query, solr_filter=solr_filter, 
                               last_processed_stories_id=start, rows=offset)
        log.info('  page %d' % page),
        all_stories.extend(stories)
        if len(stories) < 1:
            break
        start = max([s['processed_stories_id'] for s in stories])
        page = page + 1
    log.info('  Retrieved {0} stories for query {1}'.format(len(all_stories), solr_query))
    return all_stories
    
# get facebook shares for all the stories in the topic
@cache
def fetch_share_counts(tid, continueid):
    storybatch = mca.topicStoryList(tid, limit=500, link_id = continueid)
    shares = [(s['stories_id'], s['facebook_share_count']) for s in storybatch['stories']]
    continuation = storybatch['link_ids'] # for paging through results
    return shares, continuation

log.info('reading topicStoryList for facebook shares')
fbshares_start = time.time()
fbshares = [] # facebook shares indexed by stories_id
continuationid = None

while True:
    log.info('continuation_id: {0}'.format(continuationid))
    log.info('{0} stories found so far'.format(len(fbshares)))
    
    shares, continuation = fetch_share_counts(CONTROVERSY_ID, continuationid)
    fbshares += shares

    #if no more results, no "next" page id in continuation dictionary
    if len(shares) == 0 or 'next' not in continuation: 
        break
    
    continuationid = continuation['next']

fbshares = dict(fbshares)

time_spent_fbshares = float(time.time() - fbshares_start)

# set up a csv to record all the story urls
story_url_csv_file = open(os.path.join(dest_dir,'mpv-controversy-stories.csv'), 'wb') # use 'wb' for windows, 'w' otherwise
fieldnames = ['full_name', 'first_name', 'last_name', 'sex', 'date_of_death', 'age', 'city', 'state', 'cause', 'population', 
              'story_date', 'stories_id', 'media_id','media_name', 'bitly_click_count', 'facebook_share_count', 'url', 'num_sentences' ]
story_url_csv = unicodecsv.DictWriter(story_url_csv_file, fieldnames = fieldnames, 
    extrasaction='ignore', encoding='utf-8')
story_url_csv.writeheader()

# set up a csv to record counts of all the stories per person
story_count_csv_file = open(os.path.join(dest_dir,'mpv-controversy-story-counts.csv'), 'wb') # use 'wb' for windows, 'w' otherwise
fieldnames = ['full_name', 'story_count' ]
story_count_csv = unicodecsv.DictWriter(story_count_csv_file, fieldnames = fieldnames, 
    extrasaction='ignore', encoding='utf-8')
story_count_csv.writeheader()

# iterate over all the queries grabbing stories and queing a req for bitly counts
time_spent_querying = 0
time_spent_queueing = 0
for person in data:
    log.info("Working on %s" % person['full_name'])

    #if person['full_name']!="Akai Gurley":
    #   continue
    # build the in-controversy query for stories about this person
    query = "{~ topic:"+CONTROVERSY_ID+"}"

    name_key = person['full_name']
    if name_key in custom_query_keywords:
        log.info("  adjustment: %s -> %s" % (name_key,custom_query_keywords[name_key]))
        query += " AND " +custom_query_keywords[name_key]
    elif 'first_name' in person.keys() and 'last_name' in person.keys():
        query += ' AND "{0}" AND "{1}"'.format(person['first_name'], person['last_name']) 
    else:
        query += ' AND "{0}"'.format(person['full_name'])

    query_filter = build_mpv_daterange(person['date_of_death'])

    # fetch the stories
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
        #if db.storyExists(story['stories_id']):
        #    log.debug("    story in db already %s" % story['stories_id'])
        #    continue;
        # now go ahead and save it
        story_data = copy.deepcopy(person)
        story_data['story_date'] = story['publish_date']
        story_data['stories_id'] = story['stories_id']
        story_data['url'] = story['url']
        story_data['bitly_click_count'] = story['bitly_click_count']
        story_data['facebook_share_count'] = fbshares[int(story['stories_id'])]
        story_data['media_id'] = story['media_id']
        story_data['media_name'] = story['media_name']
        story_data['num_sentences'] = len(mca.story(story['stories_id'], sentences=True)['story_sentences'])
        story_url_csv.writerow(story_data)
        story_url_csv_file.flush()
        # now figure out how to save it
        #existing_story = db.getStory(story['stories_id'])
        log.debug("    found story %s" % story['stories_id'])
        #db.addStory(story,story_data)

    story_count_csv.writerow({'full_name':person['full_name'],'story_count':len(stories)-duplicate_stories})
    story_count_csv_file.flush()
    
    log.info("  Started with %d stories" % len(stories))
    log.info("    skipped %d stories that have duplicate urls" % duplicate_stories)
    queue_duration = float(time.time() - queue_start)
    time_spent_queueing = time_spent_queueing + queue_duration
    
# log some stats about the run
duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
log.info("  took %d seconds to look up fb shares" % time_spent_fbshares)
log.info("  took %d seconds to query" % time_spent_querying )
log.info("  took %d seconds to queue" % time_spent_queueing )

#log.info("There are %d stories total in the db" % db.storyCount())

story_count_csv_file.close()
story_url_csv_file.close()