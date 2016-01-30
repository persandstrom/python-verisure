# python-verisure
A python module for reading and changing status of verisure devices through mypages. Compatible with both Python2 (2.6+) and Python3.

### Legal Disclaimer
This software is not affiliated with Verisure Holding AB and the developers take no legal responsibility for the functionality or security of your Verisure Alarms and devices.

### supported devices:
    alarm (get, set)
    climate (get)
    ethernet (get)
    heatpump (get)
    lock (get, set)
    mousedetection (get)
    smartcam (get)
    smartplug (get, set)
    vacationmode (get)


## Command line usage

```
usage: verisure.py [-h] username password {get,set} ...

Read or change status of verisure devices

positional arguments:
  username    MySite username
  password    MySite password
  {get,set}   commands
    get       Read status of one or many device types
    set       Set status of a device
```

### Read alarm status

``` python verisure.py user@example.com mypassword get alarm ```

output:

```
alarm
	status: unarmed
	notAllowedReason: 
	changeAllowed: True
	label: Disarmed
	date: Today 7:10 AM
	type: ARM_STATE
	id: 1
	name: Alex Poe
```

### Read status from all devices

``` python verisure.py user@example.com mypassword get all ```

### Disarm

``` python verisure.py user@example.com mypassword set alarm 1234 DISARMED ```

### Turn on smartplug 

``` python verisure.py user@example.com mypassword set smartplug '5AC2 4LXH' on ```


## Module usage

### Installation
``` pip install vsure ```
or
``` pip install git+https://github.com/persandstrom/python-verisure.git ```


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
