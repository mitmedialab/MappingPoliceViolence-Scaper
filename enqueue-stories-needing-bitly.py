import mpv.extender

# set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.info("---------------------------------------------------------------------------")

mpv.extender.enqueue_tasks('bitly_clicks','add_bitly_clicks')
