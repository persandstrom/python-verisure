# python-verisure
A python3 module for reading and changing status of verisure devices through verisure app API.

### Legal Disclaimer
This software is not affiliated with Verisure Holding AB and the developers take no legal responsibility for the functionality or security of your Verisure Alarms and devices.


### Version History
```
2.1.0 Add door-lock-configuration command
2.0.0 Move to GraphQL API, major changes
1.0.0 Move to app-API, major changes
```

## Installation
``` pip install vsure ```
or
``` pip install git+https://github.com/persandstrom/python-verisure.git ```


## Command line usage

```
Usage: python -m verisure [OPTIONS] USERNAME PASSWORD

  Read and change status of verisure devices through verisure app API

Options:
  -i, --installation INTEGER      Installation number
  -c, --cookie TEXT               File to store cookie in
  --arm-away CODE                 Set arm status away
  --arm-home CODE                 Set arm state home
  --arm-state                     Read arm state
  --broadband                     Get broadband status
  --capability                    Get capability
  --charge-sms                    Charge SMS
  --climate                       Get climate
  --disarm CODE                   Disarm alarm
  --door-lock DEVICELABEL         Get door lock status
  --door-lock-configuration DEVICELABEL
                                  Get door lock configuration 
  --door-unlock <DEVICELABEL CODE>...
                                  Unlock door
  --door-window                   Read status of door and window sensors
  --fetch-all-installations       Fetch installations
  --guardian-sos                  Guardian SOS
  --is-guardian-activated         Is guardian activated
  --permissions                   Permissions
  --poll-arm-state <TRANSACTIONID FUTURESTATE>...
                                  Poll arm state
  --poll-lock-state <TRANSACTIONID DEVICELABEL FUTURESTATE>...
                                  Poll lock state
  --remaining-sms                 Get remaing number of SMS
  --set-smartplug <DEVICELABEL BOOLEAN>...
                                  Set state of smart plug
  --smart-button                  Get smart button state
  --smart-lock                    Get smart lock state
  --smartplug DEVICELABEL         Read status of a single smart plug
  --smartplugs                    Read status of all smart plugs
  --user-trackings                Read user tracking status
  --help                          Show this message and exit.

```

### Read alarm status

``` vsure user@example.com mypassword --arm-state ```

output:

```
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

### Read status from alarm and door-window

``` vsure user@example.com mypassword --arm-state --door-window ```


# DEPRICATED BELOW THIS LINE


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
