# `export GOOGLE_APPLICATION_CREDENTIALS=./GoogleSpreadsheetAccess-be765243bfb4.json`
import logging, os, sys, time, json, datetime, copy
from oauth2client.client import GoogleCredentials

import mediacloud
from mpv import basedir, config, mc, incidents
from mpv.util import build_mpv_daterange

# set up logging
logging.basicConfig(filename=os.path.join(basedir,'logs','mpv-queries.log'),level=logging.DEBUG)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
start_time = time.time()
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.INFO)
mc_logger = logging.getLogger('mediacloud')
mc_logger.setLevel(logging.INFO)

data = incidents.get_all()
custom_query_keywords = incidents.get_query_adjustments()

# iterate over all the queries grabbing stories and queing a req for bitly counts
queries = []
for person in data:
    log.info("Working on %s" % person['full_name'])
    query = ""
    name_key = person['first_name']+' '+person['last_name']
    if name_key in custom_query_keywords:
        log.info("  adjustment: %s -> %s" % (name_key,custom_query_keywords[name_key]))
        query = custom_query_keywords[name_key]
    else:
        query = '"{0}" AND "{1}"'.format(person['first_name'], person['last_name'])

    # a) limit query to correct date range only
    # query_filter = build_mpv_daterange(row)
    # b) also limit query to us media sources (msm, regional, partisan sets)
    query_filter = build_mpv_daterange(person['date_of_death']) + " AND (tags_id_media:(8875027 2453107 129 8878292 8878293 8878294)) "
    # c) also limit query to non-spidered us media sources (msm, regional, partisan sets)
    # query_filter = build_mpv_daterange(row) + " AND (tags_id_media:(8875027 2453107 129 8878292 8878293 8878294)) " + " AND NOT (tags_id_stories:8875452) " 
    queries.append("("+query+" AND "+query_filter+")")
    
log.info("Giant combined query is:")
log.info(" OR ".join(queries))

# log some stats about the run
duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
