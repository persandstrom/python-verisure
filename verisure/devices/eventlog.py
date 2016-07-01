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
            parser.feed(self._session.get(
                EVENTLOG_ITEMS_URL,
                to_json=False,
                eventlogPage=page,
                offset=offset))
        return parser.eventlog


class EventlogParser(HTMLPARSER):
    """ Parse relevant information from HTML response """
    def __init__(self):
        HTMLPARSER.__init__(self)
        self.eventlog = []
        self.eventlogitem = {}
        self.recording = False

    def handle_starttag(self, tag, attributes):
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

    def handle_data(self, data):
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
            self.eventlogitem['details'] = data.strip()
            self.eventlog.append(self.eventlogitem)
            self.eventlogitem = {}
