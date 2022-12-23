# panda3d-screenrecorder
An easy screen recorder that works with panda3d, and offers instant replay functionality.

This screen recorder currently supports the .mp4 format, and is threaded so as to be non-blocking to your game/program logic. The screen recorder saves live image data from your game/program into a Python dictionary which is kept at constant size, giving you instant access to the last 30 seconds or so of your gameplay.

## Prerequisites
- panda3d-1.10.13 (or higher)
- opencv-python

## Usage
Press 'p' to initiate the instant replay recording, once `setup_sg(base)` has been called.
```python
import pandarecord  # this is the individual local file "pandarecord" containing the program definitions

base = ShowBase()
pandarecord.setup_sg(base)  # setup_sg(input_np, output_file = 'screencap_vid', buff_hw = [512,256], use_clock = False)
```

As of the initial version, you will need to add your own folder "caps/" to your working program directory. 

## TODO
- Fix the ram image --> numpy --> opencv process so that we don't have to write to disk before video creation.
- Offer improved fine tuning for FOV, framerate, aspect ratio, video length, and so on.
- Make a PyPI package
