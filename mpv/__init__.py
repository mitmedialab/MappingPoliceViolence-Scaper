import os, ConfigParser

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
