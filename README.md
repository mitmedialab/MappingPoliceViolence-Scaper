Mapping Police Violence Scraper
===============================

Script to pull in articles and bitly counts realted to our Mapping Police Violence study.

Installation
------------

First install the dependences: `pip install -r requirements.pip`

Then install the `bitly-story-counts` branch of the [MediaCloud-API repo](https://github.com/c4fcm/MediaCloud-API-Client/tree/bitly-story-counts).

Make sure you set up a `GoogleSpreadsheetAccess....json` file with permissions for the spreadsheet.

Copy `app.config.template` to `app.config` and put in your MC api key.

Running
-------

First export the google permissions: `export GOOGLE_APPLICATION_CREDENTIALS=./GoogleSpreadsheetAccess....json`.

Then run the script `python mpc_generate_story_data.py`.

And you can talk the `.log` or `.csv` that are created to keep an eye on the results.
