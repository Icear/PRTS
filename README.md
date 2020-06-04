# Arkngihts Auto Fight Script

This is a script to do some repetitive work such as 1-7.

Warning: This script is made only for personal interest to verify what I have learnd. Using this script may lead to account ban. **Use this script at your own risk**


## How it works

The script takes screenshot via ADB command and compares it with preset template to distinguish which status it is, and takes corresponding action by sending tap command to simulate actual tap action.

Here are the status that script could be able to distinguish:
- level_selection
    - restore_sanity_medicine
    - restore_sanity_stone
- team_up
- fighting
- battle_settlement
    - annihilation_settlement
    - level_up

Now the function has to work with proper template set up in single resolution, I'll try to overcome the resolution limit in the future. (It's still a huge mess inside the code XD)

## Requirements

- ADB(Android Debug Bridge)
- Python 3.7+

## Install

```
git clone https://github.com/Icear/AutoFighter
cd AutoFighter
pip3 install -r ./requirements.txt
```
## Pre-setup

### Set up emulator

- for BlueStack emulator
    - check "Enable Android Debug Bridge(ADB)" at setting menu
    - restart your emulator (make sure the setting takes effect)
    - script shuold be able to connect to your emulator from now on

- for other emulator
    - turn to your emulator provider for the way to connect your emulator to ADB

- for phone user
    - connect your phone with usb cable or use wireless debug
    - make sure device is visiable throught ADB and script will work just good

script will keep waiting for device util you connect a device to ADB

### Set up template

The script comes with preset template working on 1920x980 and 1600x900(not full support) resolution on Chinese server

If you need the script to work on other resolution or other language server, you can use 'GenerateTemplate.py' script to generate new template for your resolution
- change the target template name you want to generate at the end line of 'GenerateTemplate.py'
- execute it
- it will automatically take an screenshot from your device and show up
- find the template location, click the top left corner then click the bottom right corner and press any key
- the cut template should show up in a new pop window, press any key again and script will automatically save the cut template to template folder
- ~~move it to the template folder~~
- you are good to go
  
## Usage

Choose the target level you want to run, make sure the auto deploy box checked, then run the script.
(the script is able to catch up in the middle of gaming, so you can actually run the script at any moment during the game)

To run script with limited times, for example 3 times.
> python ArknightsAutoFighter.py -t 3

To run script with unlimited times and disallow to use medicine to restore sanity.
> python ArknightsAutoFighter.py -m false # because run times is set to 0 by default
or 
> python ArknightsAutoFighter.py -t 0 -m false.

To run script with unlimited times and allow to use medicine to restore sanity
> python ArknightsAutoFighter.py # because medicine is set to allow by default
or
> python ArknightsAutoFighter.py -t 0 -m true.

Use 'python ArknightsAutoFighter.py -h' for more introduction.

