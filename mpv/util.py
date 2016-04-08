import datetime

def _zi_time(d):
    return datetime.datetime.combine(d, datetime.time.min).isoformat() + "Z"

def build_mpv_daterange(date_of_death):
    # from 5 days before the event, to 2 weeks afterwards
    date_object = datetime.datetime.strptime(date_of_death, '%Y-%m-%d')
    death_date = _zi_time(date_object)
    before_date = date_object - datetime.timedelta(days=5)
    start_date = before_date.strftime('%Y-%m-%d')
    two_weeks_post_death = date_object + datetime.timedelta(days=14)
    date_range = '(publish_date:[{0} TO {1}])'.format(_zi_time(before_date), _zi_time(two_weeks_post_death))
    return date_range
