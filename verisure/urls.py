"""
Verisure urls.
"""

import base64
import requests
import json


# pylint: disable=missing-docstring
try:
    # Python 3
    from urllib.parse import quote_plus
except ImportError:
    # Python 2
    from urllib import quote_plus

BASE_URLS = ['https://m-api01.verisure.com', 'https://m-api02.verisure.com']
BASE_URL = None
BASIC_AUTH_HEADERS = {'Accept': 'application/json;charset=UTF-8', 'Content-Type': 'application/xml;charset=UTF-8'}


def login(username, password):
    return requests.post(
        '{base_url}/auth/login'.format(base_url=BASE_URL),
        headers=BASIC_AUTH_HEADERS,
        auth=(username, password)
        )


def fetch_all_installations(username):
    return {
        "operationName": "fetchAllInstallations",
        "variables": {"email": username},
        "query": '''query fetchAllInstallations($email: String!) {
            account(email: $email) {
                installations {
                    giid
                    alias
                    pinCodeLength
                }
            }
        }'''
    }
        

def user_trackings(giid):
    return {
        "operationName": "userTrackings",
        "variables": {"giid": giid},
        "query": '''query userTrackings($giid: String!) {
            installation(giid: $giid) {
                userTrackings {
                    isCallingUser
                    webAccount
                    status
                    xbnContactId
                    currentLocationName
                    deviceId
                    name
                    initials
                    currentLocationTimestamp
                    deviceName
                    currentLocationId
                    __typename
                }
                __typename
            }
        }'''
    }

def climate(giid):
    return {
        "operationName": "Climate",
        "variables": {"giid": giid},
            "query": '''query Climate($giid: String!) {
                installation(giid: $giid) {
                    climates {
                        device {
                            deviceLabel
                            area
                            gui {
                                label
                                __typename
                            }
                            __typename
                        }
                        humidityEnabled
                        humidityTimestamp
                        humidityValue
                        temperatureTimestamp
                        temperatureValue
                        thresholds {
                            aboveMaxAlert
                            belowMinAlert
                            sensorType
                            __typename
                        }
                        __typename
                    }
                    __typename
                }
            }'''
    }


def door_window(giid):
    return {
        "operationName": "DoorWindow",
        "variables": {"giid": giid},
            "query": '''query DoorWindow($giid: String!) {
                installation(giid: $giid) {
                    doorWindows {
                        device {
                            deviceLabel
                            __typename
                        }
                        type
                        area
                        state
                        wired
                        reportTime
                        __typename
                    }
                    __typename
                }
            }'''
    }


def arm_state(giid):
    return {
        "operationName": "ArmState",
        "variables": {"giid": giid},
            "query": '''query ArmState($giid: String!) {
                installation(giid: $giid) {
                    armState {
                        type
                        statusType
                        date
                        name
                        changedVia
                        __typename
                    }
                    __typename
                }
            }'''
    }


def broadband(giid):
    return {
        "operationName": "Broadband",
        "variables": {"giid": giid},
            "query": '''query Broadband($giid: String!) {
                installation(giid: $giid) {
                    broadband {
                        testDate
                        isBroadbandConnected
                        __typename
                    }
                    __typename
                }
            }'''
    }

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


def history(guid):
    return ('{base_url}/celapi/customereventlog/installation/{guid}'
            + '/eventlog').format(
                base_url=BASE_URL,
                guid=guid)


def get_lockstate(guid):
    return installation(guid) + 'doorlockstate/search'


def set_lockstate(guid, device_label, state):
    return installation(guid) + 'device/{device_label}/{state}'.format(
        device_label=device_label, state=state)


def get_lockstate_transaction(guid, transaction_id):
    return (installation(guid)
            + 'doorlockstate/change/result/{transaction_id}'.format(
                transaction_id=transaction_id))


def lockconfig(guid, device_label):
    return installation(guid) + 'device/{device_label}/doorlockconfig'.format(
        device_label=device_label)


def imagecapture(guid, device_label):
    return (installation(guid)
            + 'device/{device_label}/customerimagecamera/imagecapture'.format(
                device_label=device_label))


def get_imageseries(guid):
    return (installation(guid)
            + 'device/customerimagecamera/imageseries/search')


def download_image(guid, device_label, image_id):
    return (installation(guid)
            + 'device/{device_label}/customerimagecamera/image/{image_id}/'
            ).format(
                device_label=device_label,
                image_id=image_id)


def get_vacationmode(guid):
    return installation(guid) + 'vacationmode'


def get_heatpump_state(guid, device_label):
    return (installation(guid)
            + 'device/{device_label}/heatpump'
            ).format(
                device_label=device_label)


def set_heatpump_state(guid, device_label):
    return (installation(guid)
            + 'device/{device_label}/heatpump/config'
            ).format(
        device_label=device_label)


def set_heatpump_feature(guid, device_label, featurestate):
    return (installation(guid)
            + 'device/{device_label}/heatpump/config/feature/{feature}'
            ).format(
                device_label=device_label, feature=featurestate)

def get_firmware_status(guid):
    return '{base_url}/xbn/2/installation/{guid}/firmware/status'.format(
            base_url=BASE_URL,
            guid=guid)
