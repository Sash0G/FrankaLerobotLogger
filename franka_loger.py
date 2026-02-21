import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import cv2
from cv_bridge import CvBridge
import os

class Franka_loger(Node):
    def __init__(self):
        super().__init__('franka_loger')
        self.declare_parameter('logs_per_sec', 1.0)
        self.declare_parameter('number_cams', 1)
        self.declare_parameter('image_path', 'home/logger/images')
        self.current_state = []
        self.captured_states = []
        self.image_path = self.get_parameter('image_path').value
        self.logs_per_sec = self.get_parameter('logs_per_sec').value
        self.number_cams = self.get_parameter('number_cams').value
        self.timer = self.create_timer(1 / self.logs_per_sec, self.log_image)
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

    def camera_log(self, msg, cam_id):
        self.get_logger().info('Received from '+str(cam_id))
        self.current_state[cam_id]=msg

    def log_image(self):
        self.get_logger().info('Logging')
        for i in range(0,self.number_cams):
            if self.current_state[i]!=None: self.captured_states[i].append(self.current_state[i])

    def shutdown_function(self):
        #self.get_logger().info('Shutting down')
        for i in range(0,self.number_cams):
            lnn = len(self.captured_states[i])
            for j in range(0,lnn):
                cur_name = os.path.join(self.image_path, f'cam{i}_frame_{j:06d}.jpg')
                self.make_file(msg=self.captured_states[i][j],file_name=cur_name)
            #self.get_logger().info('Captured '+str(lnn))

    def make_file(self, msg, file_name):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            cv2.imwrite(file_name, cv_image)
        except Exception as e:
            print(f"Error saving {file_name}: {e}")
    


def main(args=None):
    rclpy.init(args=args)

    franka_loger = Franka_loger()

    try:
        rclpy.spin(franka_loger)
    except KeyboardInterrupt:
        franka_loger.get_logger().info('Keyboard Interrupt (Ctrl+C) - Shutting down...')
    finally:
        franka_loger.shutdown_function()
        franka_loger.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
