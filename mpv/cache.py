import hashlib, os, codecs

'''
Super basic file-based cache (utf-8 friendly).  Helpful if you're developing a 
webpage scraper and want to be a bit more polite to the server you're scraping 
while developing. The idea is that it caches content in files, each named by an 
md5 of the title you pass in.
'''

DEFAULT_DIR = "cache"

cache_dir = DEFAULT_DIR

if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

def md5_key(string):
    '''
    Use this to generate filename keys
    '''
    m = hashlib.md5()
    m.update(string)
    return m.hexdigest()

def set_dir(new_dir = DEFAULT_DIR):
    '''
    Don't need to call this, unless you want to override the default location
    '''
    global cache_dir
    cache_dir = new_dir
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

def contains(title):
    '''
    Returns true if a file named by key is in the cache dir
    '''
    key = md5_key(title)
    return os.path.isfile(os.path.join(cache_dir,key))

def get(title):
    '''
    Returns the contents of the file named by key from the cache dir.
    Returns None if file doesn't exist
    '''
    key = md5_key(title)
    if os.path.isfile(os.path.join(cache_dir,key)):
        with open(os.path.join(cache_dir,key), "r") as myfile:
            return myfile.read()
    return None

def put(title,content):
    '''
    Creates a file in the cache dir named by key, with the content in it
    '''
    key = md5_key(title)
    text_file = codecs.open(os.path.join(cache_dir,key), encoding='utf-8', mode="w")
    text_file.write(content)
    text_file.close()

def remove(title):
    key = md5_key(title)
    os.remove(os.path.join(cache_dir,key))
