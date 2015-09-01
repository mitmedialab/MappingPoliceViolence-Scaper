from __future__ import absolute_import
import json, datetime

from celery.utils.log import get_task_logger
import socialshares

import mediacloud.api
from mpv.celery import app
from mpv import mc, db, cache

log = get_task_logger(__name__)

@cache
def _get_bitly_clicks(start_ts, end_ts, story_id):
    try:
        stats = mc.storyBitlyClicks(start_ts, end_ts, stories_id=story_id)  # MC will figure out the right url
        return stats['total_click_count']
    except mediacloud.error.MCException as mce: 
        if mce.status_code==404:
            log.debug("Story %s - 404 - No clicks in bitly" % story_id)
            stats = {'total_click_count':0}
            return 0
        else:
            raise mce

@cache
def _get_social_shares(url):
    services = ['facebookfql','facebook','twitter']
    stats = socialshares.fetch(url,services)

@app.task(serializer='json',bind=True)
def add_bitly_clicks(self,story_id):
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
            total_click_count = _get_bitly_clicks(start_ts, end_ts, story_id)  # MC figure out the right url
            log.info("Story %s - %d clicks" % (story_id, total_click_count))
            log.debug("  url: %s"+story_url)
        except mediacloud.error.MCException as mce:
            if mce.status_code==429:
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
        story = db.getStory(story_id)
        stats = _get_social_shares(story['url'])
        db.updateStory(story, {'social_shares':stats})
    except Exception as e:
        log.exception("Exception - something bad happened")
        raise self.retry(exc=e)
