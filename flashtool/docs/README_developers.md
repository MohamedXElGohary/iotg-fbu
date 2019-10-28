# Keembay Firmware Update Tool Architecture
## Directory Structure
Generated using linux tree
```
fwupdate
├── fwupdate
│   ├── common
│   │   ├── configparser.py
│   │   ├── __init__.py
│   │   └── logging.py
│   ├── kbydevices
│   │   ├── bin
│   │   │   ├── fastboot
│   │   │   ├── fiptool
│   │   │   ├── libXLink.so
│   │   │   ├── xlinkdevices
│   │   │   └── xlinkdownload
│   │   └── __init__.py
│   ├── fwupdate.py
│   └── __init__.py
├── tests
│   └── test_devices.py
├── Readme.md
└── setup.py

5 directories, 14 files
```
## Design Pattern
Follows but not religiously, MVC (Model-View-Controller) pattern:
### Model
kbydevices package which contains the Device classes and each Device class should have minimum two methods, discover and download. Think this as our database where Discover==GET and download==PUT.
### Controller
fwupdate.py module. The main module of the package, which gets the requests and return the response.
### View
Taken care by Python Click library.
## Helpers
The common helpers like logging and configuration handling are in common package. Designed in this way so we can import and use it in future projects.
The interface of these libraries mimics the original so if you learn how to use the standard library, you can use them(saves time on documentation).
### logging
Basically this is Python's logging module(standard library) monkey patched with extra classes and functions.
### configparser
Basically this is Python's configparser module(standard library) monkey patched to take json file.
## To do
- subprocess.run() output to be logged: i.e. args, stdout, return code- done for download, do for devices, fip_check and error classes
- Log in pwd if log path does not exist
- The tool doesn't work well with sudo. Need to think a way to achieve this.
- strict serial no checking in case of multiple device downloading
- progress bar
- More tests. More error classes:error code strategy- do not catch an error that you dont handle
- Better docstring
- Documentation with cool graphics.
- Asynchronous programming. If multiple devices found, we don't want to flash them one by one. Wait for feedback.
- Windows support
- add to developers.md on how to create configs and loggers
- simplify config file- need a config that disables logging(default python), log file name
- implement interactive
- implement retries
- Refactor code
- logging- add handler which produces single log file per run, rotating log
- API style: all function returns are dictionary