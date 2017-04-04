# python-verisure
A python module for reading and changing status of verisure devices through verisure app API. Compatible with both Python2 (2.6+) and Python3.

### Legal Disclaimer
This software is not affiliated with Verisure Holding AB and the developers take no legal responsibility for the functionality or security of your Verisure Alarms and devices.


### Version History
```
1.3.5 Fix issue with encoding of credentials
1.3.4 Fix issue with encoding in ResponseError
1.3.3 Switch between known sub domains
1.3.2 Update base url 
1.3.1 Add LOCK and UNLOCK as filter options for event log
1.3.0 Added command for door/window status
1.2.0 CLI output as json
1.1.2 Change base host
1.1.1 Prettier printing of response error for command line usage
1.1.0 Support vacation mode 
1.0.0 Move to app-API, major changes
```

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
    vacationmode        Get vacation mode info
    door_window         Get door/window status

optional arguments:
  -h, --help            show this help message and exit
  -i INSTALLATION, --installation INSTALLATION
                        Installation number
```

### Read alarm status

``` vsure user@example.com mypassword armstate ```

output:

```
{
    "name": "Alex Poe",
    "cid": "12345678",
    "state": true,
    "changedVia": "CODE",
    "date": "2017-03-11T21:04:40.000Z",
    "statusType": "ARMED_HOME"
}
```

### Read status from all devices

``` vsure user@example.com mypassword overview ```

### Filter out door lock status from overview 

``` vsure user@example.com password overview doorLockStatusList ```

### Disarm

``` vsure user@example.com mypassword set alarm 1234 DISARMED ```

### Unlock door

``` vsure user@example.com mypassword set lock 123456 '6EA1 A422' unlock ```

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
events = session.get_history(('ARM', 'DISARM'))
session.logout()
```

