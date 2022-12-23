from panda3d.core import NodePath, Filename, PerspectiveLens
import os
import cv2
import copy
from direct.stdpy import threading2

def setup_sg(input_np, output_file = 'screencap_vid', buff_hw = [512,256], use_clock = False):
    base.buff_hw = buff_hw
    base.use_clock = use_clock
    base.win_texture_a = base.win.make_texture_buffer("win_texture_a", base.buff_hw[0], base.buff_hw[1], to_ram = True)
    win_a_sg = NodePath("win_a_scenegraph")
    base.win_a_cam = base.make_camera(base.win_texture_a, lens=PerspectiveLens(90, 5))
    win_a_sg.reparent_to(base.render)
    base.win_a_cam.reparent_to(base.cam)

    base.cap_continue = True
    base.output_file = output_file

    print('Instant replay screen recording initialized.')

    tex_initial = base.win_texture_a.get_texture()
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
        
    screengrab_task(input_np)

def cv_video_output():
    source_imgs = [img for img in os.listdir(base.cap_dir)]
    source_imgs.sort()
    frame_a = cv2.imread(base.cap_dir + source_imgs[20])
    height, width, layers = frame_a.shape

    fr = float(base.clock.get_average_frame_rate())  # this breaks the save if fr is irrationally small or so

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    if not base.use_clock:
        out_vid = cv2.VideoWriter(str(base.output_file) + '.mp4',fourcc,60,(base.buff_hw[0], base.buff_hw[1]))
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
    print('Video conversion complete.' + '\n' + 'Saving video to program dir.')
    
    for f in os.listdir(base.cap_dir):
        os.remove(base.cap_dir + f)

    base.cap_continue = True

def screen_cap_acc():
    if base.cap_continue:
        tex_a = base.win_texture_a.get_texture()
        # tex_a.set_compression(5)
        tex_a_copy = copy.deepcopy(tex_a)  # this tex deepcopy is possible as of panda3d-1.10.13
        if tex_a.has_ram_image():
            tex_a_copy.set_ram_image(tex_a.get_ram_image())

        base.screens[base.screen_num] = tex_a_copy

        if len(base.screens) > 3000:  # prevent image dict from growing arbitrarily large
            first_key = list(base.screens.keys())[0]
            for x in range(1000):
                base.screens.pop(first_key)
                first_key += 1
        
    base.screen_num += 1

def screen_cap_accum(task):
    screen_cap_acc()

    return task.cont

def output_accum_screens():
    base.cap_continue = False
    print('Instant replay recording initiated.' + '\n' + 'Working...')
    
    def iter_textures():
        for num, img in base.screens.items():
            try:
                img.write(Filename('caps/' + str(num) + '.png'))
            except:
                if num != 1000:
                    print('Image ' + str(num) + ' failed.')
            
        del base.screens
        base.screens = {}

        print('Finished writing images.' + '\n' + 'Beginning video conversion.')

        cv_video_output()

    threading2._start_new_thread(iter_textures, ())

def screengrab_task(input_np):
    input_np.task_mgr.add(screen_cap_accum)
    input_np.accept('p', output_accum_screens)
