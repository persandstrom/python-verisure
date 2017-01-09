# python-verisure
A python module for reading and changing status of verisure devices through verisure app API. Compatible with both Python2 (2.6+) and Python3.

### Legal Disclaimer
This software is not affiliated with Verisure Holding AB and the developers take no legal responsibility for the functionality or security of your Verisure Alarms and devices.


### Version History
1.0.0 Move to app-API, major changes


## Installation
``` pip install vsure ```
or
``` pip install git+https://github.com/persandstrom/python-verisure.git ```


## Command line usage

```
usage: verisure.py [-h] [-i INSTALLATION]
                   username password
                   {installations,overview,set,history,eventlog,capture,imageseries,getimage}
                   ...

Read or change status of verisure devices

positional arguments:
  username              MyPages username
  password              MyPages password
  {installations,overview,set,history,eventlog,capture,imageseries,getimage}
                        commands
    installations       Get information about installations
    overview            Read status of one or many device types
    armstate            Get arm state
    set                 Set status of a device
    climate             Get climate history
    eventlog            Get event log
    capture             Capture image
    imageseries         Get image series
    getimage            Download image

optional arguments:
  -h, --help            show this help message and exit
  -i INSTALLATION, --installation INSTALLATION
                        Installation number
```

### Read alarm status

``` vsure user@example.com mypassword armstate ```

output:

```
{'area': 'REMOTE',
 'changedVia': 'REMOTE_APP',
 'cid': '12345678',
 'date': '2017-01-04T21:26:22.000Z',
 'name': 'Alex Poe',
 'state': True,
 'statusType': 'ARMED_HOME'}
```

### Read status from all devices

``` vsure user@example.com mypassword overview ```

### Disarm

``` vsure user@example.com mypassword set alarm 1234 DISARMED ```

### Turn on smartplug 

``` vsure user@example.com mypassword set smartplug '5AC2 4LXH' on ```

### Get event log with filter for arm and disarm events

``` vsure user@example.com mypassword eventlog -f ARM DISARM ```

## Module usage

### Read alarm status


```
import verisure

session = verisure.Session('user@example.com', 'password')
session.login()
armstate = session.get_arm_state()
session.logout()
print(armstate["statusType"])
```

### Set alarm status
```
import verisure

session = verisure.Session('user@example.com', 'password')
session.login()
session.set_arm_state('1234', 'ARMED_HOME')
session.logout()
```

### Turn on smartplug
```
import verisure

session = verisure.Session('user@example.com', 'password')
session.login()
session.set_smartplug_state('1A2B 3C4D', True)
session.logout()
```

### Read status of all devices
```
import verisure

session = verisure.Session('user@example.com', 'password')
session.login()
overview = session.get_overview()
session.logout()
```

### Get event log
```
import verisure

session = verisure.Session('user@example.com', 'password')
session.login()
events = session.get_history()
session.logout()
```

