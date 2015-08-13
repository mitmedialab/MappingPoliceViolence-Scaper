import logging, unicodecsv, time, os, json, sys

import mpv.tasks
from mpv import basedir, db

# set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
start_time = time.time()

stories_with_data = db._db.stories.find( { 'bitly_clicks': {'$exists': True} }).count();
stories_needing_data = db._db.stories.find( { 'bitly_clicks': {'$exists': False} }).count();

log.info("Found %d stories " % db.storyCount())
log.info("  %d stories with data" % stories_with_data)
log.info("  %d stories needing data" % stories_needing_data)

queued_stories = 0
for story in db._db.stories.find( { 'bitly_clicks': {'$exists': False} }):
    mpv.tasks.save_from_id.delay(story['stories_id'])
    queued_stories = queued_stories + 1
    log.debug("  queued %s"+str(story['stories_id']))

duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
log.info("  queue %d stories" % queued_stories)
