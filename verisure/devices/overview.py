"""
Overview of device, deynamically created from the device attributes
"""


class Overview(object):
    ''' mypages device overview

        Args:
            overview_type (str): Type of device
            status (str): the json returned from mypages

    '''

    def __init__(self, overview_type, status):
        self.__dict__.update(status)
        self._overview_type = overview_type

    def get_typename(self):
        """ get the type of device

            Returns (str): name of the device type

        """

        return self._overview_type

    def get_status(self):
        ''' get all status items as a dict

            Returns (dict): All status items as a dict

        '''

        return [(key, value) for (key, value)
                in self.__dict__.items() if not key.startswith('_')]
