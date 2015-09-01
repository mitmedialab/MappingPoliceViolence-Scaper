Mapping Police Violence Scraper
===============================

Script to pull in articles and bitly counts realted to our Mapping Police Violence study.

Installation
------------

First install the dependences: `pip install -r requirements.pip`

Then install the `bitly-story-counts` branch of the [MediaCloud-API repo](https://github.com/c4fcm/MediaCloud-API-Client/tree/bitly-story-counts).

Make sure you set up a `GoogleSpreadsheetAccess....json` file with permissions for the spreadsheet.

Now you need to set up a Redis queue somewhere:
* On OSX you should use [homebrew](http://brew.sh) - `brew install redis`.
* On Unbuntu, do `apt-get install redis-server` (the config file ends up in `/etc/redis/redis.conf`).

You also need to set up Mongo somewhere, because that is where the results are stored.

Copy `app.config.template` to `app.config` and fill it in with your info.

Running
-------

There are three pieces here:
1. fetch all the stories and dump them into a Mongo database
2. grab stories from db needing bitly counts and pass them off to Celery/Redis to add in those counts 
3. grab stories from db needing facebook/twitter counts and pass them off to Celery/Redis to add in those counts 
4. run a script that reads the db and writes the combined results into a csv
Here's instructions for each step.

## 1. Fetching Stories

First export the google permissions: `export GOOGLE_APPLICATION_CREDENTIALS=./GoogleSpreadsheetAccess....json`.

To fetch all the stories and push them into a Redis queue, run `fetch-stories.py`.  Note that this caches the story results into the `cache` dir, so if you want to start from scratch delete that dir first! You can tail the `fetcher.log` or `mpv_story_urls.csv` to see how it is going.

As you might guess, this will give you a `mpv_story_urls.csv` that lists all the stories it found.

This will be faster if you add an index to the mpv.stories collection:
```mongo
use mpv
db.stories.createIndex( { "stories_id": 1 }, { unique: true } )`
```

## 2. Adding Bitly Counts

Run `python enqueue-stories-needing-bitly.py` to push them into a Redis queue, which is polled by Celery to a pool of workers that query MC for the bitly counts.  Start the Celery worker like this: `celery -A mpv worker -l info`.

## 3. Adding Facebook/Twitter counts

Run `python enqueue-stories-needing-social-shares.py` to push them into a Redis queue, which is polled by Celery to a pool of workers that query MC for the bitly counts.  Start the Celery worker like this: `celery -A mpv worker -l info`.

## 4. Generating Results

To generate a CSV listing all the results, run `write-results.py`.

Extra Notes
-----------

If you set up Celery as a [service on Ubuntu](http://celery.readthedocs.org/en/latest/tutorials/daemonizing.html#init-script-celeryd) then you can run `sudo service celeryd start` to start the service:
* copy the [daemon script](https://raw.githubusercontent.com/ask/celery/master/contrib/generic-init.d/celeryd) to `/etc/init.d/celeryd' and make it executable
* copy the [example configuration](http://celery.readthedocs.org/en/latest/tutorials/daemonizing.html#example-configuration) to `/etc/default/celeryd` and change the `CELERYD_NODES` name to something you will recognize, change `CELERY_BIN` and `CELERY_CHDIR` to point at your virtualenv, set `CELERYD_LOG_LEVEL= "DEBUG"` if you want more logging
* create a new unpriveleged celery user: `sudo groupadd celery; sudo useradd -g celery celery`

If you need to empty out all your queues, just `redis-cli -n 0 flushdb` (where 0 is the DB number you've set in the `app.config` file).
