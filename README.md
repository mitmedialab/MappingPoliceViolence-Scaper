Mapping Police Violence Scraper
===============================

Script to aggregate data from our investigation with Black Lives Matter into Police Violence in 2014.

Installation
------------

First install the dependences: `pip install -r requirements.pip`

If you haven't already, install Redis for [Linux](http://redis.io/download) or [Windows](https://github.com/MSOpenTech/redis).

If you haven't already, follow the instructions in steps 1 and 2 [here](https://developers.google.com/sheets/quickstart/python) and download the indicated client_secret.json file to the 'mpv' subfolder.

Make a copy of `app.config.template` and fill it in with your info. Rename it `app.config`. 

Process
-------

### 1. Generate Story Counts and Seed Query

Run `count-story-totals.py` to create `data/YEAR/mpv-total-story-counts.csv`.  This file inclues a list of:
 * each victim's name
 * the total number of stories published from the sources in the time period
 * the number of stories from the sources that were about the victim in the time period
 * the normalized number of stories from the sources that were about the victim in the time period
 * the query terms that specified the victim's name
 * the query filter that was used to specify the sources and the time period

It writes giant combined queries to files in `data/YEAR/`, which we used to create the unspidered topic.  This takes about 10 minutes on my laptop.

### 2. Create the Controversy

Run mc.storyCount() on the giant query in the `data/YEAR/query-with-names.txt` file you created to make sure that the number of stories is reasonable. Then ask the core team to create a controversy by sending them that txt file. Once it is ready you'll need the numeric controversy id.  We do this to capture bit.ly click counts so we can evaluate social sharing over time.

* controversy_id for 2014: 1326
* controversy_id for 2015: 1394 
* controversy_id for 2016: 1408

### 3. Generate the Outputs

Run `list-all-stories.py` to generate a list of all the stories in the topic we created (`data/YEAR/mpv-controversy-stories.csv`) and totals by victim (`data/YEAR/mpv-controversy-story-counts.csv`). This took about 25 minutes for me. Manually check some random names in the spreadsheet to ensure that the stories are on-topic, and remove the necessary story ids from the topic in the Topic Mapper tool. Once the topic is regenerated, run `list-all-stories.py` again to generate clean story data.

Run `count-coverage.py` to generate the attention over time data, saved to `data/YEAR/mpv-sentences-over-time.csv`. This takes a few seconds.
