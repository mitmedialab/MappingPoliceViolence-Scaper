from __future__ import absolute_import
import json, datetime

from celery.utils.log import get_task_logger
import socialshares

import mediacloud.api
import mpv.cache
from mpv.celery import app
from mpv import mc, db

log = get_task_logger(__name__)

USE_CACHE = True

@app.task(serializer='json',bind=True)
def save_from_id(self,story_id):
    try:
        cache_key = str(story_id)+"_bitly_stats"
        story = db.getStory(story_id)
        story_id = story['stories_id']
        story_url = story['url']
        total_click_count = None
        now = datetime.datetime.now()
        max_range = datetime.timedelta(days=1000)
        start_ts = (now - max_range).strftime('%s')
        end_ts = datetime.date.today().strftime('%s')
        retry = False
        try:
            stats = mc.storyBitlyClicks(start_ts, end_ts, stories_id=story_id)  # MC figure out the right url
            mpv.cache.put(cache_key,json.dumps(stats))
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
        # add in the bitly data to the record already in the db
        db.updateStory(story, {'bitly_clicks':total_click_count})
    except Exception as e:
        log.exception("Exception - something bad happened")
        raise self.retry(exc=e)

@app.task(serializer='json',bind=True)
def add_social_shares(self,story_id):
    try:
        services = ['facebookfql','facebook','twitter']
        #cache_key = str(story_id)+"_social_stats"
        story = db.getStory(story_id)
        stats = socialshares.fetch(story['url'],services)
        db.updateStory(story, {'social_shares':stats})
        #mpv.cache.put(cache_key,json.dumps(stats))
    except Exception as e:
        log.exception("Exception - something bad happened")
        raise self.retry(exc=e)
