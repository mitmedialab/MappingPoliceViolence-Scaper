import os, ConfigParser
import hermes.backend.redis
import mediacloud

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# load the settings file
config = ConfigParser.ConfigParser()
config.read(os.path.join(basedir, 'app.config'))

# create the output dir
dest_dir = os.path.join(basedir,'data',config.get('spreadsheet','year'))
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# glocal mediacloud connection
mc = mediacloud.api.MediaCloud(config.get('mediacloud','key'))

# initialize the cache
cache = hermes.Hermes(hermes.backend.redis.Backend, ttl=31104000, host='localhost', 
    db=int(config.get('cache','redis_db_number')))
