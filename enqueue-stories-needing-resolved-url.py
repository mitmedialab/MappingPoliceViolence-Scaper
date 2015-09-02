import logging

import mpv.extender

# set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")

mpv.extender.enqueue_tasks('resolved_url','add_resolved_url')
