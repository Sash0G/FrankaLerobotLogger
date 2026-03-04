import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import Image
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32
import cv2
import pandas as pd
from cv_bridge import CvBridge
import os
import numpy as np
import threading
import sys
import subprocess
import time
import signal


class Franka_loger(Node):
    def __init__(self):
        super().__init__('franka_loger')
        self.declare_parameter('fps', 1.0)
        self.declare_parameter('number_cams', 1)
        self.declare_parameter('directory_path', '/workspace/logger')
        self.declare_parameter('start_delay', 1.0)
        self.declare_parameter('cameras_path', '/workspace/ros2/src/franka_loger/config/config_camera')
        self.curently_logging = True
        self.current_joints = None
        self.current_gello = None
        self.current_gripper = None
        self.captured_joints = []
        self.current_image = []
        self.captured_images = []
        self.cameras_path = self.get_parameter('cameras_path').value
        self.start_delay = self.get_parameter('start_delay').value
        self.image_path = self.get_parameter('directory_path').value+'/images'
        self.joints_path = self.get_parameter('directory_path').value+'/joints'
        self.fps = self.get_parameter('fps').value
        self.number_cams = self.get_parameter('number_cams').value
        self.init_timer = self.create_timer(self.start_delay, self.begin_timer)
        self.my_subscriptions = []
        self.bridge = CvBridge()

        if not os.path.exists(self.image_path):
            os.makedirs(self.image_path)
        if not os.path.exists(self.joints_path):
            os.makedirs(self.joints_path)

        for i in range(0, self.number_cams):
            self.my_subscriptions.append(None)
            self.current_image.append(None)
            self.captured_images.append([])
            text = '/cam'+str(i)+'/image_raw'
            self.my_subscriptions[i] = self.create_subscription(
                Image,
                text,
                lambda msg, cam_id=i: self.camera_log(msg, cam_id),
                10)

        self.my_subscriptions.append(self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_log,
            10))
        self.my_subscriptions.append(self.create_subscription(
            JointState,
            '/gello/joint_states',
            self.gello_log,
            10))
        
        self.my_subscriptions.append(self.create_subscription(
            Float32,
            '/gripper/gripper_client/target_gripper_width_percent',
            self.gripper_log,
            10))
        
    def stop_logging(self):
        self.curently_logging=False
    
    def start_logging(self):
        self.curently_logging=True

    def begin_timer(self):
        self.init_timer.cancel()
        self.timer = self.create_timer(1 / self.fps, self.frame_log)

    def camera_log(self, msg, cam_id):
        self.current_image[cam_id] = msg

    def gello_log(self, msg):
        self.current_gello = np.array(msg.position, dtype=np.float32)

    def gripper_log(self, msg):
        self.current_gripper = msg.data

    def joint_log(self, msg):
        timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        self.current_joints = (timestamp,np.array(msg.position, dtype=np.float32))

    def frame_log(self):
        if not self.curently_logging:
            return
<<<<<<< HEAD
        #self.get_logger().info('Logging')
        if self.current_gripper is None:
            self.get_logger().warn(f'\033[31mNot getting joint from gripper.\033[0m')
            return
=======
        self.get_logger().info('Logging')
>>>>>>> f66644727e0feaf51c30141908fc8a921de51d2f
        if self.current_joints is None:
            self.get_logger().warn(f'\033[31mNot getting joints from robot.\033[0m')
            return
        if self.current_gello is None:
            self.get_logger().warn(f'\033[31mNot getting joints from gello.\033[0m')
            return                     
        timestamp, joints = self.current_joints
        current_gripper_cp = self.current_gripper
        self.captured_joints.append([timestamp,*(joints[:-2]),self.current_gripper,*self.current_gello,current_gripper_cp])
        for i in range(0, self.number_cams):
            if self.current_image[i] != None:
                self.captured_images[i].append(self.current_image[i])
            else:
                self.get_logger().warn(f'\033[31mCamera {i} not working\033[0m')

    def put_in_file(self, episode_num, episode_descr):
        if len(self.captured_joints)==0:
            print('There is nothing to encode.')
            return

        print('Begining to encode.')
        for i in range(0, self.number_cams):
            video_name = os.path.join(
                self.image_path, f'episode{episode_num:04d}_cam{i:04d}_video.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            first_img = self.bridge.imgmsg_to_cv2(
                self.captured_images[i][0], desired_encoding='bgr8')
            height, width, _ = first_img.shape
            video_writer = cv2.VideoWriter(
                video_name, fourcc, self.fps, (width, height))
            for msg in self.captured_images[i]:
                cv_img = self.bridge.imgmsg_to_cv2(
                    msg, desired_encoding='bgr8')
                video_writer.write(cv_img)
            video_writer.release()
            print(f'Done video of cam {i}')
        # the current algorithm only looks at gello_joint cus we still havent looked at how
        # to find the actual joint states, it sets the current value as joint
        # for action it iterates forward as long as the array is monotone, and puts the last
        # action that breaks the monotomy. In essence if you are closing, it puts the last
        # value of the closing and action
        for i in range(0,len(self.captured_joints)):
            if i==(len(self.captured_joints)-1):
                self.captured_joints[i][16]=self.captured_joints[i][8]
            elif self.captured_joints[i][8]==self.captured_joints[i+1][8]:
                self.captured_joints[i][16]=self.captured_joints[i][8]
            elif self.captured_joints[i][8]<self.captured_joints[i+1][8]:
                fin = i
                for j in range(i,len(self.captured_joints)):
                    if j==(len(self.captured_joints)-1):
                        fin=j
                        break
                    if self.captured_joints[j+1][8]<=self.captured_joints[j][8]:
                        fin=j
                        break
                self.captured_joints[i][16]=self.captured_joints[fin][8]
            else:
                fin = i
                for j in range(i,len(self.captured_joints)):
                    if j==(len(self.captured_joints)-1):
                        fin=j
                        break
                    if self.captured_joints[j+1][8]>=self.captured_joints[j][8]:
                        fin=j
                        break
                self.captured_joints[i][16]=self.captured_joints[fin][8]
        columns = ['timestamp'] + [f'joint{i}' for i in range(1,9)] + [f'action{i}' for i in range(1,9)]
        df = pd.DataFrame(self.captured_joints, columns=columns)
        df["episode_descr"] = episode_descr
        parquet_path = os.path.join(self.joints_path, f'episode{episode_num:04d}_joints.parquet')
        df.to_parquet(parquet_path,index=False)
        print('Joints saved')
        print(f'Completed episode capture of episode {episode_num}')
        self.captured_joints.clear()
        for image_array in self.captured_images:
            image_array.clear()

def spin_node(loger): #the idea is that ros complains when you shut him down externally, so i remove the complaining by catching the error
        try:
            rclpy.spin(loger)
        except ExternalShutdownException: 
            pass

def check_cameras(cam_proceses):
    for proces in cam_proceses:
        if proces.poll() is not None:
            return False
    return True

def main(args=None):

    if '--params-file' not in sys.argv:
        print("No YAML provided. Loading default config '/workspace/ros2/src/franka_loger/config/logger_params.yaml']")
        sys.argv.extend(['--ros-args', '--params-file', '/workspace/ros2/src/franka_loger/config/logger_params.yaml'])

    rclpy.init(args=args)

    franka_loger = Franka_loger()

    spin_thread = None
    cam_proceses = []

    try:
        print('Launching Cameras')
        for i in range(0,franka_loger.number_cams):
            config_name = franka_loger.cameras_path+f'{i}.yaml'
<<<<<<< HEAD
            cam_command = ['ros2', 'run', 'usb_cam', 'usb_cam_node_exe', '--ros-args', '--params-file', config_name, '-r', f'/image_raw:=/cam{i}/image_raw', '-r', f'__node:=usb_cam{i}' ]
            cur_process = subprocess.Popen(cam_command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            time.sleep(1)
            if cur_process.poll() is not None:
                print(f'Couldn\'t launch camera {i}')
                saved_output, saved_errors = cur_process.communicate()
                print(saved_output.strip())
                print(saved_errors.strip())
=======
            cam_command = ['ros2', 'run', 'usb_cam', 'usb_cam_node_exe', '--ros-args', '--params-file', config_name, '-r', f'/image_raw:=/cam{i}/image_raw' ]
            cur_process = subprocess.Popen(cam_command,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            time.sleep(1)
            if cur_process.poll() is not None:
                print(f'Couldn\'t launch camera {i}')
>>>>>>> f66644727e0feaf51c30141908fc8a921de51d2f
                for proces in cam_proceses:
                    if proces.poll() is None:
                        pgid = os.getpgid(proces.pid)
                        os.killpg(pgid, signal.SIGKILL)
                        proces.wait()
                if rclpy.ok():
                    rclpy.shutdown()
                franka_loger.destroy_node()
                return
            print(f'Launched camera {i}')
            cam_proceses.append(cur_process)
        cur_episode_num = 0
        while True:
            try_num = input('Enter First Episode Number.\n')
            if try_num.isdigit():
                cur_episode_num = int(try_num)
                break
            print('Pleas enter a proper integer.')
        cur_episode_descr = input(f'Enter Description of episode {cur_episode_num}.\n')
        print(f'Beginning logging and Episode {cur_episode_num}.\n')
        spin_thread = threading.Thread(target=spin_node, args=(franka_loger,), daemon=True) #this is the threading, daemon=True means to kill the thread if loger.py dies
        spin_thread.start()
        franka_loger.start_logging()
        while True:
            end_episode = input(f'Enter anything to end episode {cur_episode_num}.\n')
            franka_loger.stop_logging()
            try:
                franka_loger.put_in_file(episode_num=cur_episode_num,episode_descr=cur_episode_descr)
            except Exception as error:
                print(str(error))
            print(f'Ended episode{cur_episode_num}.\n')
            if not check_cameras(cam_proceses):
                print('Not all cameras are working.\n')
                break
<<<<<<< HEAD
            inp2 = input('Output YES if you want to redo episode')
            if inp2!='YES': 
                cur_episode_num+=1
=======
            cur_episode_num+=1
>>>>>>> f66644727e0feaf51c30141908fc8a921de51d2f
            inp = input(f'Enter Description of episode {cur_episode_num} or leave empty to repeat previous.\n')
            if inp:
                cur_episode_descr = inp
            print(f'Begining Episode {cur_episode_num}.\n')
            franka_loger.start_logging()
    except KeyboardInterrupt:
        print('\nKeyboard Interrupt, starting abortion.\n')
        franka_loger.destroy_node()
        print('Killing node')
        if rclpy.ok():
            rclpy.shutdown()
        for proces in cam_proceses:
            if proces.poll() is None:
                pgid = os.getpgid(proces.pid)
                os.killpg(pgid, signal.SIGKILL)
                proces.wait()
        if spin_thread!=None and spin_thread.is_alive():
            spin_thread.join() #this waits for the thread to finish

<<<<<<< HEAD
=======

    for proces in cam_proceses:
        if proces.poll() is None:
            pgid = os.getpgid(proces.pid)
            os.killpg(pgid, signal.SIGKILL)
            proces.wait()
    franka_loger.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()
    if spin_thread!=None and spin_thread.is_alive():
        spin_thread.join() #this waits for the thread to finish
>>>>>>> f66644727e0feaf51c30141908fc8a921de51d2f


if __name__ == '__main__':
    main()
