"""
Alarm device
"""
import time

OVERVIEW_URL = '/remotecontrol'
COMMAND_URL = '/remotecontrol/armstatechange.cmd'
CHECK_STATE = '/remotecontrol/checkstate.cmd'


class Alarm(object):
    """ Alarm device

    Args:
        session (verisure.session): current session
    """

    def __init__(self, session):
        self._session = session

    def set(self, code, state):
        """ set status of alarm component

            Args:
                code (str): Personal alarm code (four digits)
                state (str): 'ARMED_HOME', 'ARMED_AWAY' or 'DISARMED'

        """
        data = {
            'code': code,
            'state': state
        }
        return not self._session.post(COMMAND_URL, data)

    def wait_while_pending(self, max_request_count=100):
        """ Wait for pending alarm to finish

            Args:
                max_request_count (int): maximum number of post requests

            Returns: retries if success else -1

        """

        for counter in range(max_request_count):
            data = {'counter': counter}
            response = self._session.post(CHECK_STATE, data)
            if 'hasResult' not in response:
                break
            if 'hasPending' in response and not response['hasPending']:
                return counter
            counter = counter + 1
            time.sleep(1)
        return -1
