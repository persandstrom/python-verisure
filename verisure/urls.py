"""
Verisure urls.
"""

# pylint: disable=missing-docstring
try:
    # Python 3
    from urllib.parse import quote_plus
except ImportError as e:
    # Python 2
    from urllib import quote_plus

BASE_URLS = [
    'https://e-api01.verisure.com',
    'https://e-api02.verisure.com',
]
BASE_URL = None


def installation(guid):
    return '{base_url}/xbn/2/installation/{guid}/'.format(
        base_url=BASE_URL,
        guid=guid)


def login():
    return '{base_url}/xbn/2/cookie'.format(
        base_url=BASE_URL)


def get_installations(username):
    return '{base_url}/xbn/2/installation/search?email={username}'.format(
        base_url=BASE_URL,
        username=quote_plus(username))


def overview(guid):
    return installation(guid) + 'overview'.format(
        installation=installation)


def smartplug(guid):
    return installation(guid) + 'smartplug/state'


def set_armstate(guid):
    return installation(guid) + 'armstate/code'


def get_armstate_transaction(guid, transaction_id):
    return installation(guid) + 'code/result/{transaction_id}'.format(
        transaction_id=transaction_id)


def get_armstate(guid):
    return installation(guid) + 'armstate'


def door_window(guid):
    return installation(guid) + 'device/view/DOORWINDOW'


def history(guid):
    return ('{base_url}/celapi/customereventlog/installation/{guid}' +
            '/eventlog').format(
                base_url=BASE_URL,
                guid=guid)


def climate(guid):
    return installation(guid) + 'climate/simple/search'


def get_lockstate(guid):
    return installation(guid) + 'doorlockstate/search'


def set_lockstate(guid, device_label, state):
    return installation(guid) + 'device/{device_label}/{state}'.format(
        device_label=device_label, state=state)


def get_lockstate_transaction(guid, transaction_id):
    return (installation(guid) +
            'doorlockstate/change/result/{transaction_id}'.format(
                transaction_id=transaction_id))


def lockconfig(guid, device_label):
    return installation(guid) + 'device/{device_label}/doorlockconfig'.format(
        device_label=device_label)


def imagecapture(guid, device_label):
    return (installation(guid) +
            'device/{device_label}/customerimagecamera/imagecapture')


def get_imageseries(guid):
    return (installation(guid) +
            'device/customerimagecamera/imageseries/search')


def download_image(guid, device_label, image_id):
    return (installation(guid) +
            'device/{device_label}/customerimagecamera/image/{image_id}/'
            ).format(
                device_label=device_label,
                image_id=image_id)


def get_vacationmode(guid):
    return installation(guid) + 'vacationmode'


def test_ethernet(guid):
    return installation(guid) + 'trigger/testethernet'


def get_heatpump_state(guid, device_label):
    return (installation(guid) +
            'device/{device_label}/heatpump'
            ).format(
                device_label=device_label)


def set_heatpump_state(guid, device_label):
    return (installation(guid) +
            'device/{device_label}/heatpump/config'
            ).format(
        device_label=device_label)


def set_heatpump_feature(guid, device_label, featurestate):
    return (installation(guid) +
            'device/{device_label}/heatpump/config/feature/{feature}'
            ).format(
                device_label=device_label, feature=featurestate)
