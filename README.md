# python-verisure

A python3 module for reading and changing status of verisure devices through verisure
app API.

## Legal Disclaimer

This software is not affiliated with Verisure Holding AB and the developers take no
legal responsibility for the functionality or security of your Verisure Alarms and
devices.

## Version History

```txt
2.6.3 Differentiate response errors
2.6.2 Fix request wrapper
2.6.1 Move to automation subdomain
2.6.0 Add Get Firmware Version
2.5.6 Fix docstring, cookie lasts 15 minutes
2.5.5 Solved bug during response error except using CLI
2.5.4 Add possibility to set giid to all queries, refactoring and resolve lint warnings
2.5.3 Refactor login
2.5.2 Fix XBN Database is not activated
2.5.1 Update CLI, split cookie login to separate function, rename mfa functions
2.5.0 Add MFA login
2.4.1 Add download_image
2.4.0 Add camera support
2.3.0 Add event-log command
2.2.0 Add set-autolock-enabled command
2.1.2 Installation instructions for m-api branch
2.1.1 Cleaned up readme
2.1.0 Add door-lock-configuration command
2.0.0 Move to GraphQL API, major changes
1.0.0 Move to app-API, major changes
```

## Installation

```sh
pip install vsure
```

or 

```sh
pip install git+https://github.com/persandstrom/python-verisure.git@version-2
```

## Usage

```py
# example_usage.py

import verisure

USERNAME = "example@domain.org"
PASSWORD = "MySuperSecretP@ssword"

session = verisure.Session(USERNAME, PASSWORD)

# Login without Multifactor Authentication
installations = session.login()
# Or with Multicator Authentication, check your phone and mailbox
session.request_mfa()
installations = session.validate_mfa(input("code:"))

# Get the `giid` for your installation
giids = {
  inst['alias']: inst['giid']
  for inst in installations['data']['account']['installations']
}
print(giids)
# {'MY STREET': '123456789000'}

# Set the giid
session.set_giid(giids["MY STREET"])
```

### Read alarm status (py)

```py
arm_state = session.request(session.arm_state())
```

output

```json
{
    "data": {
        "installation": {
            "armState": {
                "type": null,
                "statusType": "DISARMED",
                "date": "2020-03-11T21:04:40.000Z",
                "name": "Alex Poe",
                "changedVia": "CODE",
                "__typename": "ArmState"
            },
            "__typename": "Installation"
        }
    }
}
```

### Read status from alarm and door-window (py)

```py
output = session.request(session.arm_state(), session.door_window())
```

output

```json
[
    {
        "data": {
            "installation": {
                "armState": {
                    "type": null,
                    "statusType": "DISARMED",
                    "date": "2022-01-01T00:00:00.000Z",
                    "name": "Alex Poe",
                    "changedVia": "CODE",
                    "__typename": "ArmState"
                },
                "__typename": "Installation"
            }
        }
    },
    {
        "data": {
            "installation": {
                "doorWindows": [
                    {
                        "device": {
                            "deviceLabel": "ABCD EFGH",
                            "__typename": "Device"
                        },
                        "type": null,
                        "area": "Front Door",
                        "state": "CLOSE",
                        "wired": false,
                        "reportTime": "2022-01-01T00:00:00.000Z",
                        "__typename": "DoorWindow"
                    },
                    {
                        "device": {
                            "deviceLabel": "IJKL MNOP",
                            "__typename": "Device"
                        },
                        "type": null,
                        "area": "Back Door",
                        "state": "CLOSE",
                        "wired": false,
                        "reportTime": "2022-01-01T00:00:00.000Z",
                        "__typename": "DoorWindow"
                    }
                ],
                "__typename": "Installation"
            }
        }
    }
]
```

## Command line usage

```txt
Usage: python -m verisure [OPTIONS] USERNAME PASSWORD

  Read and change status of verisure devices through verisure app API

Options:
  -i, --installation INTEGER      Installation number
  -c, --cookie TEXT               File to store cookie in
  --mfa                           Login using MFA
  --arm-away CODE                 Set arm status away
  --arm-home CODE                 Set arm state home
  --arm-state                     Read arm state
  --broadband                     Get broadband status
  --camera-capture <DEVICELABEL REQUESTID>...
                                  Capture a new image from a camera
  --camera-get-request-id DEVICELABEL
                                  Get requestId for camera_capture
  --cameras                       Get cameras state
  --cameras-image-series          Get the cameras image series
  --cameras-last-image            Get cameras last image
  --capability                    Get capability
  --charge-sms                    Charge SMS
  --climate                       Get climate
  --disarm CODE                   Disarm alarm
  --door-lock <DEVICELABEL CODE>...
                                  Lock door
  --door-lock-configuration DEVICELABEL
                                  Get door lock configuration
  --door-unlock <DEVICELABEL CODE>...
                                  Unlock door
  --door-window                   Read status of door and window sensors
  --event-log                     Read event log
  --fetch-all-installations       Fetch installations
  --firmware                      Get firmware information
  --guardian-sos                  Guardian SOS
  --is-guardian-activated         Is guardian activated
  --permissions                   Permissions
  --poll-arm-state <TRANSACTIONID FUTURESTATE>...
                                  Poll arm state
  --poll-lock-state <TRANSACTIONID DEVICELABEL FUTURESTATE>...
                                  Poll lock state
  --remaining-sms                 Get remaing number of SMS
  --set-autolock-enabled <DEVICELABEL BOOLEAN>...
                                  Enable or disable autolock
  --set-smartplug <DEVICELABEL BOOLEAN>...
                                  Set state of smart plug
  --smart-button                  Get smart button state
  --smart-lock                    Get smart lock state
  --smartplug DEVICELABEL         Read status of a single smart plug
  --smartplugs                    Read status of all smart plugs
  --user-trackings                Read user tracking status
  --help                          Show this message and exit.
```

### Read alarm status (cli)

```sh
vsure user@example.com mypassword --arm-state
```

The output is the same as above [Read alarm status (py)](#read-alarm-status-py)

```json
{
    "data": {
        "installation": {
            "armState": {
                "type": null,
                "statusType": "DISARMED",
                "date": "2020-03-11T21:04:40.000Z",
                "name": "Alex Poe",
                "changedVia": "CODE",
                "__typename": "ArmState"
            },
            "__typename": "Installation"
        }
    }
}
```

### Read status from alarm and door-window (cli)

```sh
vsure user@example.com mypassword --arm-state --door-window
```
