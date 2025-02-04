from panda3d.core import NodePath, Filename, PerspectiveLens, Texture
import os
import cv2
import copy
import io
import numpy
from PIL import Image
from direct.stdpy import threading2
import time


#class to add general panda3d screen recording that works for buffers or the whole window. Ram mode is always active, be careful with max frames.

###USAGE###

#class my_game(Showbase):
#   def __init__(self):
#       ...
#       #create screen recorder to record the whole screen
#       self.screen_recorder = PandaRecorder(self)
#   
#       #change some settings
#       self.screen_recorder.setup_recorder(output_file="screen_recording_01")
#
#       #record a buffer instead
#       self.new_buffer = self.win.makeTextureBuffer("buf", 1920, 1080, to_ram=True, fbp = fbprops)
#       self.screen_recorder = PandaRecorder(self, self.new_buffer)


class PandaRecorder():
    def __init__ (self, game_showbase_instance, buffer = None, custom_resolution = None):
        self.game = game_showbase_instance
        self.buffer = buffer # this is the panda3d buffer we want to record from, as in the return value of "base.win.make_texture_buffer"

        if (not buffer == None):
            self.pandarecord_use_native = False 
            self.x = self.buffer.getXSize()
            self.y = self.buffer.getYSize()
            
        else:
            self.pandarecord_use_native = True #we will use win.get_screenshot() for the frame 
            self.x = self.game.win.getXSize()
            self.y = self.game.win.getYSize()
            print(f"game window size {self.x}, {self.y}")

        self.resize = False

        if custom_resolution == None:
            self.resolution = [self.x, self.y]
        else:
            self.resolution = custom_resolution
            self.resize = True
            print("screen recorder resize = True")

        self.cap_continue = True
        self.frame_ready = False
        self.screen_num = 1000
        self.screens = {}

        self.saved_images = [] #this holds the screenshots
            
        #setup with defaults, call separately to change
        self.setup_recorder()
        
    #setup function to set additional settings (or change the name of the video for a new recording and not overwrite the first one)
    def setup_recorder(self, output_file='screencap_vid',max_screens=5000,cust_fr=None):
        self.max_screens = max_screens
        self.cust_fr = cust_fr
        self.output_file = output_file

  



    ### INSTANT REPLAY SECTION ###
    # video is encoded at the end for maximum speed
    # but all frames kept in ram (ram usage high)
    # best to keep the frame count (max_screens) low
    def record_frame_task(self, task):
        if self.cap_continue: 
            self.record_frame()
        return task.cont

    def record_frame(self):
        if self.pandarecord_use_native:
            tex_a = self.game.win.get_screenshot()
        else:
            tex_a = self.buffer.get_texture() 

        if tex_a.has_ram_image():
            try:
                # Get the RAM image as a numpy array
                ram_image = tex_a.get_ram_image_as("BGRA")
                image_array = numpy.frombuffer(ram_image, dtype=numpy.uint8)
                self.saved_images.append(image_array.tobytes())
            except Exception as e:
                print(f"Error copying frame {self.screen_num}: {e}")
        else:
            print("No RAM image! Failed to copy frame.")

        if len(self.saved_images) > self.max_screens:
                self.saved_images.pop(0)

    def save_frames_to_video_file(self):
        self.cap_continue = False
        print('Instant replay output started.' + '\n' + 'Working...')
        threading2._start_new_thread(self.cv_video_output, ())

    def cv_video_output(self):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fr = float(self.game.clock.get_average_frame_rate())
        
        print('The current average framerate: ' + str(round(fr, 1)))
        if not (self.cust_fr == None):
            fr = self.cust_fr
        out_vid = cv2.VideoWriter(str(self.output_file) + '.mp4',fourcc,fr,(self.resolution[0], self.resolution[1]))

        for img_bytes in self.saved_images:
            img_array = numpy.frombuffer(img_bytes, dtype=numpy.uint8)
            img_array = img_array.reshape((self.y, self.x, 4))
            upside_down_img = cv2.cvtColor(numpy.array(img_array), cv2.COLOR_BGRA2BGR)
            frame = cv2.flip(upside_down_img, 0)
            if self.resize:
                frame_r = cv2.resize(frame, (self.resolution[0], self.resolution[1]), interpolation=cv2.INTER_CUBIC)
                out_vid.write(frame_r)
            else:
                out_vid.write(frame)

        del self.saved_images
        self.saved_images = []

        self.cap_continue = True
        print('video file created. ' + str(self.output_file) + '.mp4')

    

    #### KEYBOARD COMMANDS SECTION  ####
    #add a keyboard command to call these functions to start and stop recording
    #use the reset methods to clear the video and restart
    #record frames is running by default unless paused
    def run_record_frames_task(self):
        if not self.cap_continue:
            self.cap_continue = True

    def pause_record_frames_task(self):
        if self.cap_continue:
            self.cap_continue = False




    #### REALTIME CAPTURE SECTION ####
    # for realtime encoding (slower, less ram), call this and then call "realtime frame grab" every frame or use the task
    # grabbing the frame and writing it to a file happen in separate threads for speed
    def setup_video_file(self):
        self.resize = False
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fr = float(self.game.clock.get_average_frame_rate())
        print('The current average framerate: ' + str(round(fr, 1)))
        if not (self.cust_fr == None):
            fr = self.cust_fr
        self.out_vid = cv2.VideoWriter(str(self.output_file) + '.mp4',self.fourcc,fr,(self.resolution[0], self.resolution[1]))
        self.frame_ready = False
        self.cap_continue = True
        self.start_realtime_frame_processing_thread()
        self.frame_buffer = []

    def reset_video_file(self):
        self.run_encode_thread = False

    #this thread waits for a frame to be ready and then saves it
    def start_realtime_frame_processing_thread(self):
        self.run_encode_thread = True
        threading2._start_new_thread(self.realtime_threaded_encode, ())

    #optional: use this task or call realtime_frame_grab from within your own.
    def realtime_frame_grab_task(self, task):
        if self.cap_continue:
            self.realtime_frame_grab()
        return task.cont

    #grabs the frame from panda and signals to the encode thread that a frame is ready
    #warning: if your framerate is so high that it is faster than the encode, frames may be dropped
    def realtime_frame_grab(self):
        if self.pandarecord_use_native:
            tex_a = self.game.win.get_screenshot()
        else:
            tex_a = self.buffer.get_texture() 
        if tex_a.has_ram_image():
            try:
                # Get the RAM image as a numpy array
                ram_image = tex_a.get_ram_image_as("BGRA")
                self.img_array = numpy.frombuffer(ram_image, dtype=numpy.uint8)
            except:
                print("frame output failed")
        self.frame_ready = True 

    #encodes the frame with opencv, runs on thread 
    def realtime_threaded_encode(self):
        while self.run_encode_thread:
            if self.frame_ready:
                img_array = self.img_array.reshape((self.y, self.x, 4))
                upside_down_img = cv2.cvtColor(numpy.array(img_array), cv2.COLOR_BGRA2BGR)
                frame = cv2.flip(upside_down_img, 0)
                if self.resize:
                    frame_r = cv2.resize(frame, (self.resolution[0], self.resolution[1]), interpolation=cv2.INTER_CUBIC)
                    self.out_vid.write(frame_r)
                else:
                    self.out_vid.write(frame)
                self.frame_ready = False
            else:
                time.sleep(0.005)
        self.out_vid.release()








        