# PRTS


## How it works


## Requirements

- ADB(Android Debug Bridge)
- Python 3.8+
- paddleOCR
- numpy
- opencv

## Install

```
git clone https://github.com/Icear/PRTS
cd PRTS
pip3 install -r ./requirements.txt
```
Note: Before processing dependencies, you need Microsoft Visual C++ 14.0 or greater is installed in your computer. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/

## Pre-setup

### Set up emulator

- for BlueStack emulator
    - check "Enable Android Debug Bridge(ADB)" at setting menu
    - restart your emulator (make sure the setting takes effect)
    - script should be able to connect to your emulator from now on

- for other emulator
    - turn to your emulator provider for the way to connect your emulator to ADB

- for phone user
    - connect your phone with usb cable or use wireless debug
    - make sure device is visible through ADB and script will work just good

The `adb devices` command should show your device name.

Write this name to code `utils.controller.ADBController.py`, update line 31 and line 40 for your connect command

Now you are ready to go.

## Usage

### Normal run

when your emulator setup, start PRTS.py script for normal run.

```shell
python3 ./PRTS.py
```

### Test Environment

#### check OCR environment status

- open emulator
- run Script `TestPaddleOCR.py` for OCR environment check
- if `PaddleOCR` is running normally, script will show current emulator screenshot with ocr result
