import logging, time

from mpv import basedir, db
import mpv.tasks

def enqueue_tasks(db_property_name, task_function_name):
    start_time = time.time()

    task_to_call = getattr(mpv.tasks, task_function_name)

    stories_with_data = db._db.stories.find( { db_property_name: {'$exists': True} }).count();
    stories_needing_data = db._db.stories.find( { db_property_name: {'$exists': False} }).count();

    logging.info("Ready to enqueue stories for '%s' (saving as %s)" % (task_function_name,db_property_name) )
    logging.info("  Found %d stories " % db.storyCount())
    logging.info("    %d stories with data" % stories_with_data)
    logging.info("    %d stories needing data" % stories_needing_data)

    queued_stories = 0
    for story in db._db.stories.find( { db_property_name: {'$exists': False} }):
        task_to_call.delay(story['stories_id'])
        queued_stories = queued_stories + 1
        logging.debug("  queued %s"+str(story['stories_id']))

    duration_secs = float(time.time() - start_time)
    logging.info("Finished!")
    logging.info("  took %d seconds total" % duration_secs)
    logging.info("  queued %d stories" % queued_stories)
