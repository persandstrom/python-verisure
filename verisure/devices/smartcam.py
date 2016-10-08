"""
Smartcam device
"""


from .overview import Overview

OVERVIEW_URL = '/overview/camera'
CAPTURE_URL = '/picturelog/camera/{}/capture.cmd'
IMAGES_URL = '/picturelog/seriespage/0'
DOWNLOAD_URL = '/camera/{}/image/{}.jpg'


class Smartcam(object):
    """ Smartcam device

    Args:
        session (verisure.session): Current session
    """

    def __init__(self, session):
        self._session = session

    def get(self):
        """ Get device overview """
        status = self._session.get(OVERVIEW_URL)
        return [Overview('smartcam', val) for val in status]

    def download_image(self, device_id, image_id):
        """Download a image from mypages smartcam."""
        image = self._session.download(DOWNLOAD_URL.format(
            device_id.upper().replace(' ', '%20'),
            image_id))
        return image

    def get_imagelist(self):
        """ Get a list of current images from the device """
        status = self._session.get(IMAGES_URL)
        for key in status:
            if key == 'totalAmount':
                total_images = status['totalAmount']
                print('Total amount of images available for download:',
                      total_images)
        image_series = status['imageSeries']
        image_data_list = [li['images'] for li in image_series]
        n = len(image_data_list)
        image_ids = []
        for i in range(0, n):
            image_id = [li['id'] for li in image_data_list[i]]
            image_ids.append(image_id)
        print("Image_id's to use for download:", image_ids)
        return image_ids

    def capture(self, device_id):
        """Capture a new image to mypages

            Args:
                device_id (str): smartcam device id
        """
        data = {}
        return not self._session.post((CAPTURE_URL.format(
            device_id.upper().replace(' ', '%20'))), data)
