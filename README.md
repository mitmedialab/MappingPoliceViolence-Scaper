Mapping Police Violence Scraper
===============================

Script to aggregate data from our investigation with Black Lives Matter into Police Violence in 2014.

Installation
------------

First install the dependences: `pip install -r requirements.pip`

If you haven't already, install Redis for [Linux](http://redis.io/download) or [Windows](https://github.com/MSOpenTech/redis).

If you haven't already, follow the instructions in steps 1 and 2 [here](https://developers.google.com/sheets/quickstart/python) and download the indicated client_secret.json file to the 'mpv' subfolder.

Make a copy of `app.config.template` and fill it in with your info. Rename it `app.config`. 

Running
-------

### Generating Story Counts and Seed Query

Run `count-story-totals.py` to create `data/mpv-total-story-counts.csv`.  This file inclues a list of:
 * each victim's name
 * the total number of stories published from the sources in the time period
 * the number of stories from the sources that were about the victim in the time period
 * the normalized number of stories from the sources that were about the victim in the time period
 * the query terms that specified the victim's name
 * the query filter that was used to specify the sources and the time period

It writes giant combined queries to files in `data`, which we used to create the unspidered controversy.  This took about 10 minutes on my laptop.

### Listing Stories

Run `list-all-stories.py` to generate a list of all the stories in the controversy we created (`data/mpv-controvery-stories.csv`).
