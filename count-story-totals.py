import logging, os, sys, time, json, datetime, copy, unicodecsv
from oauth2client.client import GoogleCredentials
import mediacloud
from mpv import basedir, config, mc, incidentsv4, cache
from mpv.util import build_mpv_daterange

# set up logging
logging.basicConfig(filename=os.path.join(basedir,'logs','count-story-totals.log'),level=logging.DEBUG)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
start_time = time.time()
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.INFO)
mc_logger = logging.getLogger('mediacloud')
mc_logger.setLevel(logging.INFO)

data = incidentsv4.get_all()
custom_query_keywords = incidentsv4.get_query_adjustments()

# set up a csv to record all the story urls
story_count_csv_file = open(os.path.join(basedir,'data','mpv-total-story-counts.csv'), 'w')
fieldnames = ['full_name', 'date_of_death', 'total_stories', 'stories_about_person', 'normalized_stories_about_person', 'query', 'filter' ]
story_count_csv = unicodecsv.DictWriter(story_count_csv_file, fieldnames = fieldnames, 
    extrasaction='ignore', encoding='utf-8')
story_count_csv.writeheader()

# @cache - DISABLE CACHING FOR NOW - CAN'T GET THIS TO WORK ON MY MACHINE - ALLAN
def count_stories(q,fq):
    return mc.storyCount(q,fq)['count']

# iterate over all the queries grabbing stories and queing a req for bitly counts
queries = []
for person in data:
    log.info("Working on %s" % person['full_name'])
    query = ""
    name_key = person['full_name']
    if name_key in custom_query_keywords:
        log.info("  adjustment: %s -> %s" % (name_key,custom_query_keywords[name_key]))
        query = custom_query_keywords[name_key]
    elif 'first_name' in person.keys() and 'last_name' in person.keys():
        query = '"{0}" AND "{1}"'.format(person['first_name'], person['last_name']) 
    else:
        query = '"{0}"'.format(person['full_name'])

    # limit query to correct date range and us media sources (msm, regional, partisan sets)
    query_filter = build_mpv_daterange(person['date_of_death']) + " AND (tags_id_media:(8875027 2453107 129 8878292 8878293 8878294)) "
    # also limit query to non-spidered us media sources (msm, regional, partisan sets)
    # query_filter = build_mpv_daterange(row) + " AND (tags_id_media:(8875027 2453107 129 8878292 8878293 8878294)) " + " AND NOT (tags_id_stories:8875452) " 
    queries.append("("+query+" AND "+query_filter+")")
    
    data = {}
    data['full_name'] = name_key
    data['date_of_death'] = person['date_of_death']
    data['total_stories'] = count_stories('*',query_filter)
    data['stories_about_person'] = count_stories(query,query_filter)
    normalized_story_count = float(data['stories_about_person']) / float(data['total_stories'])
    data['normalized_stories_about_person'] = "{0:.15f}".format(normalized_story_count)
    data['query'] = query
    data['filter'] = query_filter
    story_count_csv.writerow(data)
    story_count_csv_file.flush()

log.info("Giant combined query is:")
log.info(" OR ".join(queries))

# log some stats about the run
duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
