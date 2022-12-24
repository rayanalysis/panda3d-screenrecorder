# panda3d-screenrecorder
An easy screen recorder that works with panda3d, and offers instant replay functionality.

This screen recorder currently supports the .mp4 format, and is threaded so as to be non-blocking to your game/program logic. The screen recorder saves live image data from your game/program into a Python dictionary which is kept at constant size, giving you instant access to the last 30 seconds or so of your gameplay.

When RAM_mode=True the recording will be performed entirely in system RAM , which gives a significant performance improvement. See the Usage sample for a listing of all the optional inputs to pandarecord.setup_sg() . Set max_screens=int(some_int) to limit the amount of RAM committed to the image dictionary.

## Prerequisites
- panda3d-1.10.13 (or higher)
- opencv-python

## Usage
Press 'p' to initiate the instant replay recording, once `setup_sg(base)` has been called.
```python
import pandarecord  # this is the individual local file "pandarecord" containing the program definitions

base = ShowBase()
pandarecord.setup_sg(base)  # setup_sg(input_np,output_file='screencap_vid',buff_hw=[512,256],use_clock=False,RAM_mode=False,max_screens=5000,cust_fr=60)
```

If you are not using RAM_mode=True , you will need to create the folder caps/ in your program directory to allow storage of the movie frames.

## TODO
- Make a PyPI package
