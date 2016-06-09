# `export GOOGLE_APPLICATION_CREDENTIALS=./GoogleSpreadsheetAccess-be765243bfb4.json`
import logging, os, sys, time, json, datetime, copy
import requests, gspread, unicodecsv
import mediacloud
from mpv import basedir, config, mc, cache, incidentsv4, dest_dir
from mpv.util import build_mpv_daterange

CONTROVERSY_ID = config.get('mediacloud','controversy_id')

YEAR = config.get('spreadsheet','year')

# set up logging
logging.basicConfig(filename=os.path.join(basedir,'logs',
    YEAR+'count-coverage.log'),level=logging.DEBUG)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")
start_time = time.time()
requests_logger = logging.getLogger('requests')
requests_logger.setLevel(logging.INFO)
mc_logger = logging.getLogger('mediacloud')
mc_logger.setLevel(logging.INFO)

log.info("Using redis db %s as a cache" % config.get('cache','redis_db_number'))

log.info("Working from controversy %s" % CONTROVERSY_ID)

controversy_filter = "{~ controversy:"+CONTROVERSY_ID+"}"
results = mc.storyCount(controversy_filter)
log.info("  %s total stories" % CONTROVERSY_ID)

# load the queries we wrote already
our_query = None
control_query = None
with open(os.path.join(dest_dir,"query-with-names.txt"), "r") as text_file:
    our_query = controversy_filter +" AND ("+text_file.read()+")"
with open(os.path.join(dest_dir,"query-no-names.txt"), "r") as text_file:
    control_query = text_file.read()
log.info("Loaded both queries")

log.info("Counting:")
log.info("  Counting our sentences...")
our_counts = mc.sentenceCount(our_query, split=True, 
    split_start_date=YEAR+"-01-01", split_end_date=str(int(YEAR)+1)+"-01-01")
log.info("  Counting control sentences...")
control_counts = mc.sentenceCount(control_query, split=True, 
    split_start_date=YEAR+"-01-01", split_end_date=str(int(YEAR)+1)+"-01-01")
log.info("Done")

# remove the annoying keys that make using the data harder
del(our_counts['split']['gap'])
del(our_counts['split']['start'])
del(our_counts['split']['end'])
del(control_counts['split']['gap'])
del(control_counts['split']['start'])
del(control_counts['split']['end'])

log.info("Writing Output CSV...")

output_file = open(os.path.join(dest_dir,'mpv-sentences-over-time.csv'), 'w')
fieldnames = ['date', 'sentences_about_victims', 'total_sentences', 'pct_coverage' ]
output_csv = unicodecsv.DictWriter(output_file, fieldnames = fieldnames, 
    extrasaction='ignore', encoding='utf-8')
output_csv.writeheader()

for k in sorted(our_counts['split'].keys()):
    logging.debug("  "+str(k))
    data = {}
    data['date'] = k
    data['sentences_about_victims'] = our_counts['split'][k]
    data['total_sentences'] = control_counts['split'][k]
    if data['total_sentences'] is 0:
        data['pct_coverage'] = 0
    else:   
        value = float(data['sentences_about_victims'])/float(data['total_sentences'])
        data['pct_coverage'] = "%.10f" % (value)
    output_csv.writerow(data)

duration_secs = float(time.time() - start_time)
log.info("Finished!")
log.info("  took %d seconds total" % duration_secs)
