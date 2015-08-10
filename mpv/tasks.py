from __future__ import absolute_import
import json, datetime

from celery.utils.log import get_task_logger

import mediacloud.api
from mpv.celery import app
from mpv import mc, db

log = get_task_logger(__name__)

POST_WRITE_BACK = True

@app.task(serializer='json',bind=True)
def save_from_id(self,story_id,data_to_save={}):
    # TODO check in DB to see if story info is already saved
    try:
        story_id = data_to_save['stories_id']
        story_url = data_to_save['url']
        now = datetime.datetime.now()
        max_range = datetime.timedelta(days=1000)
        start_ts = (now - max_range).strftime('%s')
        end_ts = datetime.date.today().strftime('%s')
        total_click_count = None
        retry = False
        try:
            stats = mc.storyBitlyClicks(start_ts, end_ts, stories_id=story_id)
            total_click_count = stats['total_click_count']
            log.info("Story %s - %d clicks" % (story_id, total_click_count))
            log.debug("  url: %s"+story_url)
        except mediacloud.error.MCException as mce:
            if mce.status_code==404:
                log.debug("Story %s - 404 - No clicks in bitly" % story_id)
                total_click_count = 0
            elif mce.status_code==429:
                log.error("Story %s - 429 - Hit the bitly API limit!" % story_id)
                retry = True
            elif mce.status_code==500:
                log.error("Story %s - 500 - MC had an error!" % story_id)
                retry = True
            else:
                log.error("Story %s - %d unknown error!" % (story_id,mce.status_code) )
                retry = True
            log.debug("  url: %s"+story_url)
            if retry:
                raise self.retry(exc=mce)
        # TODO: write results to db
        db.addStory(data_to_save, {'bitly_clicks':total_click_count})
    except Exception as e:
        log.exception("Exception - something bad happened")
        raise self.retry(exc=e)
