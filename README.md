# python-verisure
A python module for reading and changing status of verisure devices through mypages. Compatible with both Python2 (2.6+) and Python3.

### Legal Disclaimer
This software is not affiliated with Verisure Holding AB and the developers take no legal responsibility for the functionality or security of your Verisure Alarms and devices.


### Version History
1.0.0 Move to app-api, major changes


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
    set                 Set status of a device
    history             Get history of a device
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

``` vsure user@example.com mypassword overview armState ```

output:

```
armState:
  date: 2016-12-30T09:35:59+0000
  changedVia: CODE
  statusType: DISARMED
  name: Alex Poe
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

myPages = verisure.MyPages('user@example.com', 'password')
myPages.login()
alarm_overview = myPages.alarm.get()
myPages.logout()
print(alarm_overview[0].status)
```

### Set alarm status
```
import verisure

myPages = verisure.MyPages('user@example.com', 'password')
myPages.login()
myPages.alarm.set('1234', verisure.ALARM_ARMED_HOME)
myPages.alarm.wait_while_pending()
myPages.logout()
```

### Turn on smartplug
```
import verisure

myPages = verisure.MyPages('user@example.com', 'password')
myPages.login()
myPages.smartplug.set('1A2B 3C4D', verisure.SMARTPLUG_ON)
myPages.logout()
```

### Read status of all devices
```
import verisure

myPages = verisure.MyPages('user@example.com', 'password')
myPages.login()
overviews = myPages.get_overviews()
myPages.logout()
```

### Get event log
```
import verisure

myPages = verisure.MyPages('user@example.com', 'password')
myPages.login()
# read three pages of log
events = myPages.eventlog.get(pages=3)
myPages.logout()
```

