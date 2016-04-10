import os, ConfigParser
import hermes.backend.redis
import mediacloud

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# load the settings file
config = ConfigParser.ConfigParser()
config.read(os.path.join(basedir, 'app.config'))

# glocal mediacloud connection
mc = mediacloud.api.AdminMediaCloud(config.get('mediacloud','key'))

# initialize the cache
cache = hermes.Hermes(hermes.backend.redis.Backend, ttl=31104000, host='localhost', 
    db=int(config.get('cache','redis_db_number')))
