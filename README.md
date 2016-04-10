Mapping Police Violence Scraper
===============================

Script to aggregate data from our investigation with Black Lives Matter into Police Violence in 2014.

Installation
------------

First install the dependences: `pip install -r requirements.pip`

Make sure you set up a `GoogleSpreadsheetAccess....json` file with permissions for the spreadsheet.

Copy `app.config.template` to `app.config` and fill it in with your info.

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

It also logs a giant combined query that we used to create the unspidered controversy.  This took about 10 minutes on my laptop.

### Listing Stories

Run `list-all-stories.py` to generate a list of all the stories in the controversy we created (`data/mpv-controvery-stories.csv`).
