from __future__ import absolute_import

from celery import Celery
from mpv import config

app = Celery('mpv',
             broker=config.get('queue','broker_url'),
             backend=config.get('queue','backend_url'),
             include=['mpv.tasks'])

# expire backend results in one hour
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    app.start()