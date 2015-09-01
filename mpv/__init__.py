import os, ConfigParser

import hermes.backend.redis

import mediacloud

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# load the settings file
config = ConfigParser.ConfigParser()
config.read(os.path.join(basedir, 'app.config'))

mc = mediacloud.api.AdminMediaCloud(config.get('mediacloud','key'))

db = mediacloud.storage.MongoStoryDatabase(
    db_name=config.get('db','database_name'), 
    host=config.get('db','host'), 
    port=int(config.get('db','port'))
)

# initialize the cache
cache = hermes.Hermes(hermes.backend.redis.Backend, ttl=31104000, host='localhost', 
    db=int(config.get('cache','redis_db_number')))
