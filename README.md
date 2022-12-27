# panda3d-screenrecorder
An easy screen recorder that works with panda3d, and offers instant replay functionality.

This screen recorder currently supports the .mp4 format, and is threaded so as to be non-blocking to your game/program logic. The screen recorder saves live image data from your game/program into a Python dictionary which is kept at constant size. This allows instant access to a custom duration of gameplay footage.

You may specify a maximum number of stored frames, and set your framerate target. These values will determine your recording duration. You may also specify a custom resolution via buff_hw=[w,h] .

When RAM_mode=True , the recording will be performed entirely in system RAM which gives a significant performance improvement. See the Usage sample for a listing of all the optional inputs to pandarecord.setup_sg() . Set max_screens=int(some_int) to limit the amount of RAM committed to the image dictionary (default=5000).

## Prerequisites
- panda3d-1.10.13 (or higher)
- opencv-python
- numpy
- PIL

## Usage
Press 'p' to initiate the instant replay recording, once `setup_sg(base)` has been called.
```python
import pandarecord  # this is the individual local file "pandarecord" containing the program definitions

base = ShowBase()
pandarecord.setup_sg(base)  # setup_sg(input_np,output_file='screencap_vid',buff_hw=[720,400],use_clock=False,RAM_mode=True,max_screens=5000,cust_fr=60,use_native=False,write_threads=1,capture_key='p')
```

As of the current version, you will need to create the folder caps/ in your program directory to allow storage of the movie frames.

## TODO
- Make a PyPI package
