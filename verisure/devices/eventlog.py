"""
Eventlog device (not really a device)
"""

# this import is depending on python version
try:
    import HTMLParser
    HTMLPARSER = HTMLParser.HTMLParser
except ImportError:
    import html.parser
    HTMLPARSER = html.parser.HTMLParser

EVENTLOG_URL = '/uk/eventlog.html'
EVENTLOG_ITEMS_URL = '/eventlog/eventlog_items.dyn'
EVENTLOG_FILTER_URL = '/eventlog/filterEventLog.cmd'


# pylint: disable=too-few-public-methods
class Eventlog(object):
    """ Eventlog device

    Args:
        session (verisure.session): Current session
    """

    def __init__(self, session):
        self._session = session

    def get(self, pages=1, offset=0, *logfilter):
        """ Get event log

        Args:
            pages (int): Number of pages to request
            offset (int): Page offset
            *logfilter (str): [ARM,DISARM,FIRE,INTRUSION,TECHNICAL,SOS,WARNING]
        """
        self._session.get(EVENTLOG_URL, to_json=False)
        if logfilter:
            self._session.post(
                EVENTLOG_FILTER_URL,
                data={'eventLogFilter': logfilter})
        parser = EventlogParser()
        for page in range(1, pages + 1):
            result = self._session.get(
                EVENTLOG_ITEMS_URL,
                to_json=False,
                eventlogPage=page,
                offset=offset)
            parser.feed(result)
        return parser.eventlog


class EventlogParser(HTMLPARSER):
    """ Parse relevant information from HTML response """
    def __init__(self):
        HTMLPARSER.__init__(self)
        self.eventlog = []
        self.eventlogitem = {}
        self.recording = False
        self.details_join = False

    def handle_starttag(self, tag, attributes):
        self.details_join = False
        if tag != 'div':
            return
        for name, value in attributes:
            self.recording = name == 'class' and (
                value == 'eventlog-list--title' or
                value == 'eventlog-list--datetime' or
                value == 'eventlog-list--details-text hidden')

    def handle_endtag(self, tag):
        if tag == 'div':
            self.recording = False
        if self.details_join:
            self.eventlog.append(self.eventlogitem)
            self.eventlogitem = {}
            self.details_join = False

    def handle_data(self, data):
        if self.details_join:
            self.eventlogitem['details'] += data
            return
        if not self.recording or not data.strip():
            return
        if len(self.eventlogitem) == 0:
            self.eventlogitem['title'] = data.strip()
        elif len(self.eventlogitem) == 1:
            self.eventlogitem['date'] = data.strip()
        elif len(self.eventlogitem) == 2:
            self.eventlogitem['device'] = data
        elif len(self.eventlogitem) == 3:
            self.eventlogitem['location'] = data.replace('-', '').strip()
        elif len(self.eventlogitem) == 4:
            self.eventlogitem['details'] = data
            self.details_join = True
