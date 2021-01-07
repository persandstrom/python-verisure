# python-verisure
A python3 module for reading and changing status of verisure devices through verisure app API.

### Legal Disclaimer
This software is not affiliated with Verisure Holding AB and the developers take no legal responsibility for the functionality or security of your Verisure Alarms and devices.


### Version History
```
2.0.0 Move to GraphQL API, major changes
1.0.0 Move to app-API, major changes
```

## Installation
``` pip install vsure ```
or
``` pip install git+https://github.com/persandstrom/python-verisure.git ```


## Command line usage

```
Usage: vsure [OPTIONS] USERNAME PASSWORD

  Read and change status of verisure devices through verisure app API

Options:
  -i, --installation INTEGER      Installation number
  -c, --cookie TEXT               File to store cookie in
  --update_state <DEVICELABEL BOOLEAN>...
  --permissions                   No help written yet
  --user_tracking_installation_config
                                  No help written yet
  --user_trackings                No help written yet
  --capability                    No help written yet
  --broadband                     No help written yet
  --smart_button                  No help written yet
  --arm_state                     No help written yet
  --climate                       No help written yet
  --charge_sms                    No help written yet
  --remaining_sms                 Get remaing number of SMS
  --door_window                   Read status of door and window sensors
  --smart_plug DEVICELABEL        Read status of a single smart plug
  --smart_plugs                   Read status of all smart plugs
  --is_guardian_activated         No help written yet
  --guardian_sos                  No help written yet
  --fetch_all_installations       Fetch installations
  --help                          Show this message and exit.

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

``` vsure user@example.com mypassword overview doorLockStatusList ```

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

session = verisure.Session('user@example.com', 'mypassword')
session.login()
armstate = session.get_arm_state()
session.logout()
print(armstate["statusType"])
```

### Set alarm status
```
import verisure

session = verisure.Session('user@example.com', 'mypassword')
session.login()
session.set_arm_state('1234', 'ARMED_HOME')
session.logout()
```

### Turn on smartplug
```
import verisure

session = verisure.Session('user@example.com', 'mypassword')
session.login()
session.set_smartplug_state('1A2B 3C4D', True)
session.logout()
```

### Read status of all devices
```
import verisure

session = verisure.Session('user@example.com', 'mypassword')
session.login()
overview = session.get_overview()
session.logout()
```

### Get event log
```
import verisure

session = verisure.Session('user@example.com', 'mypassword')
session.login()
events = session.get_history(('ARM', 'DISARM'))
session.logout()
```