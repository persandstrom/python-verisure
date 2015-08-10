# python-verisure
A python module for reading and changing status of verisure devices through mypages. Compatible with both Python2.7 and Python3.


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
### example
Read alarm status

``` python verisure.py user@example.com mypassword get alarm ```

output:

```
AlarmStatus
	status: unarmed
	notAllowedReason: 
	changeAllowed: True
	label: Disarmed
	date: Today 7:10 AM
	type: ARM_STATE
	id: 1
	name: Alex Poe
```

set alarm status to disarmed

``` python verisure.py user@example.com mypassword set alarm DISARMED ``` 
