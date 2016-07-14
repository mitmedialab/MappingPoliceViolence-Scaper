import logging, os, sys, time, json, datetime, copy, unicodecsv
from oauth2client.client import GoogleCredentials
import mediacloud
from mpv import basedir, config, mc, incidentsv4, cache, dest_dir
from mpv.util import build_mpv_daterange

# turn off the story counting, useful if you just want to generate the giant query files
WRITE_STORY_COUNT_CSVS = True

# set up logging
logging.basicConfig(filename=os.path.join(basedir,'logs',
    config.get('spreadsheet','year')+'count-story-totals.log'),level=logging.DEBUG)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
log.info("Writing output to %s" % dest_dir)
start_time = time.time()
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.INFO)
mc_logger = logging.getLogger('mediacloud')
mc_logger.setLevel(logging.INFO)

data = incidentsv4.get_all()
custom_query_keywords = incidentsv4.get_query_adjustments()

# set up a csv to record all the story urls
if WRITE_STORY_COUNT_CSVS:
    story_count_csv_file = open(os.path.join(dest_dir,'mpv-total-story-counts.csv'), 'wb') #'wb' for windows
    fieldnames = ['full_name', 'date_of_death', 'total_stories', 'stories_about_person', 'normalized_stories_about_person', 'query', 'filter' ]
    story_count_csv = unicodecsv.DictWriter(story_count_csv_file, fieldnames = fieldnames, 
        extrasaction='ignore', encoding='utf-8')
    story_count_csv.writeheader()

@cache
def count_stories(q,fq):
    return mc.storyCount(q,fq)['count']

# iterate over all the queries grabbing stories and queing a req for bitly counts
media_filter_query = "(tags_id_media:(8875027 2453107 129 8878292 8878293 8878294))"
queries = []
no_keyword_queries = [] # for normalization
for person in data:
    log.info("  Working on %s" % person['full_name'])
    query = ""
    name_key = person['full_name']
    if name_key in custom_query_keywords:
        log.info("  adjustment: %s -> %s" % (name_key,custom_query_keywords[name_key]))
        query = custom_query_keywords[name_key]
    elif 'first_name' in person.keys() and 'last_name' in person.keys():
        query = '"{0}" AND "{1}"'.format(person['first_name'], person['last_name']) 
    else:
        query = '"{0}"'.format(person['full_name'])

    # a) limit query to correct date range only
    # query_filter = build_mpv_daterange(row)
    # b) also limit query to us media sources (msm, regional, partisan sets)
    date_range_query = build_mpv_daterange(person['date_of_death'])

    query_filter = "( " + date_range_query + " AND "+media_filter_query+" )"
    # c) also limit query to non-spidered us media sources (msm, regional, partisan sets)
    # query_filter = build_mpv_daterange(row) + " AND (tags_id_media:(8875027 2453107 129 8878292 8878293 8878294)) " + " AND NOT (tags_id_stories:8875452) " 
    queries.append("("+query+" AND "+date_range_query+")")
    no_keyword_queries.append("(" + date_range_query +")")

    if WRITE_STORY_COUNT_CSVS:
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

if WRITE_STORY_COUNT_CSVS:
    story_count_csv_file.close()

# write the query files out
log.info("Writing query files to %s" % dest_dir)
with open(os.path.join(dest_dir,"query-with-names.txt"), "w") as text_file:
    our_query = " OR ".join(queries)
    our_query = media_filter_query+" AND ("+our_query+")"
    text_file.write(our_query)
with open(os.path.join(dest_dir,"query-no-names.txt"), "w") as text_file:
    control_query = " OR ".join(no_keyword_queries)
    control_query = media_filter_query+" AND ("+control_query+")"
    text_file.write(control_query)

# log some stats about the run
duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
logging.shutdown()
