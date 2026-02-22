import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge
import os

class Franka_loger(Node):
    def __init__(self):
        super().__init__('franka_loger')
        self.declare_parameter('fps', 1.0)
        self.declare_parameter('number_cams', 1)
        self.declare_parameter('image_path', '/workspace/logger/images')
        self.declare_parameter('start_delay', 1.0)
        self.declare_parameter('episode_num', 1)
        self.declare_parameter('episode_descr', 'put the apple in the box')
        self.current_state = []
        self.captured_states = []
        self.episode_num = self.get_parameter('episode_num').value
        self.episode_descr = self.get_parameter('episode_descr').value
        self.start_delay = self.get_parameter('start_delay').value
        self.image_path = self.get_parameter('image_path').value
        self.fps = self.get_parameter('fps').value
        self.number_cams = self.get_parameter('number_cams').value
        self.init_timer = self.create_timer(self.start_delay, self.begin_timer)
        self.my_subscriptions = []
        self.bridge = CvBridge()
        if not os.path.exists(self.image_path):
            os.makedirs(self.image_path)
        for i in range(0,self.number_cams):
            self.my_subscriptions.append(None)
            self.current_state.append(None)
            self.captured_states.append([])
            text = '/cam'+str(i)+'/image_raw'
            self.get_logger().info(text)
            self.my_subscriptions[i] = self.create_subscription(
                Image,
                text,
                lambda msg, cam_id=i: self.camera_log(msg, cam_id),
                 10)
            
    def begin_timer(self):
        self.init_timer.cancel()
        self.timer = self.create_timer(1 / self.fps, self.log_image)

    def camera_log(self, msg, cam_id):
        #self.get_logger().info('Received from '+str(cam_id))
        self.current_state[cam_id]=msg

    def log_image(self):
        self.get_logger().info('Logging')
        for i in range(0,self.number_cams):
            if self.current_state[i]!=None: self.captured_states[i].append(self.current_state[i])

    def shutdown_function(self):
        print('Begining to encode.')
        for i in range(0,self.number_cams):
            video_name = os.path.join(self.image_path, f'episode{self.episode_num:04d}_cam{i:04d}_video.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            first_img = self.bridge.imgmsg_to_cv2(self.captured_states[i][0], desired_encoding='bgr8')
            height, width, _ = first_img.shape
            video_writer = cv2.VideoWriter(video_name, fourcc, self.fps, (width, height))
            for msg in self.captured_states[i]:
                cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                video_writer.write(cv_img)
            video_writer.release()
            print(f'Done video of cam {i}')
        print('Completed episode capture. Shutting down.')

    # def shutdown_function(self):
    #     #self.get_logger().info('Shutting down')
    #     for i in range(0,self.number_cams):
    #         lnn = len(self.captured_states[i])
    #         for j in range(0,lnn):
    #             cur_name = os.path.join(self.image_path, f'cam{i}_frame_{j:06d}.jpg')
    #             self.make_file(msg=self.captured_states[i][j],file_name=cur_name)
    #         #self.get_logger().info('Captured '+str(lnn))

    # def make_file(self, msg, file_name):
    #     try:
    #         cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
    #         cv2.imwrite(file_name, cv_image)
    #     except Exception as e:
    #         print(f"Error saving {file_name}: {e}")
    


def main(args=None):
    rclpy.init(args=args)

    franka_loger = Franka_loger()

    try:
        rclpy.spin(franka_loger)
    except KeyboardInterrupt:
        franka_loger.get_logger().info('Keyboard Interrupt (Ctrl+C)')
    finally:
        franka_loger.shutdown_function()
        franka_loger.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
