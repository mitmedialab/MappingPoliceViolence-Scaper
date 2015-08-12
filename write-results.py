import logging, unicodecsv, time, os, json, sys

from mpv import basedir, db

# set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
start_time = time.time()

timestr = time.strftime("%Y%m%d_%H%M%S")
filename = 'mpv_story_data_{0}.csv'.format(timestr)
filepath = os.path.join(basedir, "data", filename)
log.info('Writing data to %s' % filename)

outfile = open(filepath, 'wb')
fieldnames = ['full_name', 'first_name', 'last_name', 'sex', 'date_of_death', 'age', 'city', 
                'state', 'cause', 'story_date', 'bitly_clicks', 'population', 'story_id' ]
outcsv = unicodecsv.DictWriter(outfile, fieldnames = fieldnames, 
    extrasaction='ignore', encoding='utf-8')
outcsv.writeheader()

log.info("Found %d stories" % db.storyCount())

idx = 0
for story in db._db.stories.find().sort( [['_id', -1]] ):
    if (idx % 1000) == 0:
        log.info("  at story %d" % idx)
    outcsv.writerow(story)
    outfile.flush()
    idx = idx+1

outfile.close()
duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
