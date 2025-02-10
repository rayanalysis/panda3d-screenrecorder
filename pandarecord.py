from panda3d.core import NodePath, Filename, PerspectiveLens
import os
import cv2
import copy
import io
import numpy
from PIL import Image
from direct.stdpy import threading2
import time


def setup_sg(input_np,output_file='screencap_vid',buff_hw=[720,400],use_clock=False,RAM_mode=True,max_screens=5000,cust_fr=60,use_native=False,write_threads=1,capture_key='p'):
    base.buff_hw = buff_hw
    base.use_clock = use_clock
    base.RAM_mode = RAM_mode
    base.max_screens = max_screens
    base.cust_fr = cust_fr
    base.pandarecord_use_native = use_native
    base.write_threads = write_threads
    base.capture_key = capture_key
    tex_initial = {}

    if base.pandarecord_use_native:
        base.win_texture_a = base.win.get_screenshot()
        tex_initial = base.win_texture_a

    else:
        base.win_texture_a = base.win.make_texture_buffer("win_texture_a", base.buff_hw[0], base.buff_hw[1], to_ram = True)
    
        win_a_sg = NodePath("win_a_scenegraph")
        base.win_a_cam = base.make_camera(base.win_texture_a, lens=base.camLens)
        win_a_sg.reparent_to(base.render)
        base.win_a_cam.reparent_to(base.cam)

        tex_initial = base.win_texture_a.get_texture()

    base.cap_continue = True
    base.output_file = output_file

    print('Instant replay screen recording initialized.')

    base.screen_num = 1000
    base.screens = {}
    base.screens[base.screen_num] = tex_initial

    img_dir = 'caps/'
    
    try:
        base.cap_dir = os.path.join(img_dir)
    except:
        os.makedirs(os.path.join('caps'))
        base.cap_dir = os.path.join(img_dir)
        
    # make sure /caps folder is empty
    for f in os.listdir(base.cap_dir):
        os.remove(base.cap_dir + f)
        
    screengrab_task(input_np, base.capture_key)

def cv_video_output():
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fr = float(base.clock.get_average_frame_rate())
    
    if not base.RAM_mode:
        print('The current average framerate: ' + str(round(fr, 1)))
        source_imgs = [img for img in os.listdir(base.cap_dir)]
        source_imgs.sort()
        frame_a = cv2.imread(base.cap_dir + source_imgs[0])
        height, width, layers = frame_a.shape
        
        if not base.use_clock:
            out_vid = cv2.VideoWriter(str(base.output_file) + '.mp4',fourcc,base.cust_fr,(base.buff_hw[0], base.buff_hw[1]))
        elif base.use_clock:
            out_vid = cv2.VideoWriter(str(base.output_file) + '.mp4',fourcc,fr,(base.buff_hw[0], base.buff_hw[1]))

        for i in sorted(os.listdir(base.cap_dir)):
            try:
                frame = cv2.imread(base.cap_dir + i)
                frame_r = cv2.resize(frame, (base.buff_hw[0], base.buff_hw[1]), interpolation=cv2.INTER_CUBIC)
                out_vid.write(frame_r)
            except:
                print('Frame may have been empty, passing.')

        out_vid.release()
        print('Video conversion complete.' + '\n' + 'Saving video to program dir (last update).')
        
        for f in os.listdir(base.cap_dir):
            os.remove(base.cap_dir + f)

        base.cap_continue = True
        
    elif base.RAM_mode:
        print('The current average framerate: ' + str(round(fr, 1)))
        sorted_screens = {key: val for key, val in sorted(base.screens.items(), key = lambda element: element[0])}

        if not base.use_clock:
            out_vid = cv2.VideoWriter(str(base.output_file) + '.mp4',fourcc,base.cust_fr,(base.buff_hw[0], base.buff_hw[1]))
        elif base.use_clock:
            out_vid = cv2.VideoWriter(str(base.output_file) + '.mp4',fourcc,fr,(base.buff_hw[0], base.buff_hw[1]))

        if not base.pandarecord_use_native:
            for num, img in sorted_screens.items():
                if img.has_ram_image():
                    try:
                        img_array = Image.frombuffer('RGBA',(base.buff_hw[0], base.buff_hw[1]),img.get_ram_image_as('RGBA'),'raw','RGBA',-1,-1)
                        cv_img = cv2.cvtColor(numpy.array(img_array), cv2.COLOR_RGBA2BGR)
                        frame_r = cv2.resize(cv_img, (base.buff_hw[0], base.buff_hw[1]), interpolation=cv2.INTER_CUBIC)
                        out_vid.write(frame_r)
                    except:
                        print('Frame may have been empty, passing.')       
                    
        elif base.pandarecord_use_native:
            print('Sorry, use_native=True currently only supports RAM_mode=False' + '\n' + 'Continuing with threaded write mode.')
            for i in sorted(os.listdir(base.cap_dir)):
                try:
                    frame = cv2.imread(base.cap_dir + i)
                    frame_r = cv2.resize(frame, (base.buff_hw[0], base.buff_hw[1]), interpolation=cv2.INTER_CUBIC)
                    out_vid.write(frame_r)
                except:
                    print('Frame may have been empty, passing.')
                    
            for f in os.listdir(base.cap_dir):
                os.remove(base.cap_dir + f)
                
        out_vid.release()
        print('Video conversion complete.' + '\n' + 'Saving video to program dir (last update).')

        del base.screens
        base.screens = {}

        base.cap_continue = True

def screen_cap_acc():
    if base.cap_continue:
        if base.pandarecord_use_native:
            tex_a = base.win.get_screenshot()

        else:
            tex_a = base.win_texture_a.get_texture()

        if tex_a.has_ram_image():
            tex_a_copy = copy.deepcopy(tex_a)  # this tex deepcopy is possible as of panda3d-1.10.13
            tex_a_copy.set_ram_image(tex_a.get_ram_image())
            base.screens[base.screen_num] = tex_a_copy

        if len(base.screens) > base.max_screens:  # prevent image dict from growing arbitrarily large
            first_key = list(base.screens.keys())[0]
            for x in range(int(base.max_screens/5)):
                base.screens.pop(first_key)
                first_key += 1
        
    base.screen_num += 1

def screen_cap_accum(task):
    screen_cap_acc()

    return task.cont

def output_accum_screens():
    base.cap_continue = False
    print('Instant replay recording initiated.' + '\n' + 'Working...')

    def iter_use_native():
        if not base.RAM_mode or base.pandarecord_use_native:
            print('pandarecord RAM_mode=False ' + 'use_native=' + str(base.pandarecord_use_native) + ' Threaded write on: ' + str(base.write_threads) + ' thread(s).')
            total_record = len(base.screens)
            start_v = 1
            orig_end_v = int(round(total_record / base.write_threads))
            end_v = orig_end_v
            record_relative = []
            record_lists = []
            file_num = int(list(base.screens.keys())[0])

            for n in range(total_record):
                record_relative.append(file_num)
                file_num += 1

            for x in range(orig_end_v):
                iter_slice = slice(start_v, end_v)
                slice_list = list(record_relative[iter_slice])
                record_lists.append(slice_list)
                
                start_v += end_v
                end_v += end_v

            def seg_thread(input_list):
                for num in input_list:
                    try:
                        img = base.screens[int(num)]
                        img.write(Filename('caps/' + str(num) + '.png'))
                    except:
                        print('Key Error')

            for sub_list in record_lists:
                if not '[]' in str(sub_list):
                    threading2._start_new_thread(seg_thread, (sub_list,))


            def check_status():
                done = False
                c_history = []
                while not done:
                    c_history.append(len(os.listdir(base.cap_dir)))
                    
                    if len(c_history) > 100:
                        if c_history[0] - c_history[99] == 0:
                            done = True
                            print('Finished writing images.' + '\n' + 'Beginning video conversion.')
                            cv_video_output()

                    if len(c_history) > 200:
                         del c_history[:]
                        
                    time.sleep(0.1)

            threading2._start_new_thread(check_status, ())

        elif base.RAM_mode and not base.pandarecord_use_native:
            print('pandarecord RAM_mode=True/use_native=False')
            threading2._start_new_thread(cv_video_output, ())

    iter_use_native()

def screengrab_task(input_np, capture_key):
    base.task_mgr.add(screen_cap_accum)
    base.accept(str(capture_key), output_accum_screens)
