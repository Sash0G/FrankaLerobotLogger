import rclpy
from rclpy.node import Node
from lerobot.datasets.lerobot_dataset import LeRobotDataset
import torch
import pandas as pd
import cv2
import yaml
import argparse
from ament_index_python.packages import get_package_share_directory
import os

def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "--config",
        '-c',
        type=str,
        default = "convert_params.yaml",
        help="Name of config file"
    )

    args = parser.parse_args()
    package_share_directory = get_package_share_directory('franka_loger')
    config_file_path = os.path.join(package_share_directory, 'config', args.config)

    with open(config_file_path, "r") as f:
        config = yaml.safe_load(f)
    robot = config.get("robot",{})
    num_joints = robot.get("num_joints",7)
    if(robot.get("gripper")):
        num_joints+=1
    num_cameras = robot.get("num_cameras",2)
    directory_path = config.get("directory_path","/workspace/ros2")

    features = {
        "observation.state": {"dtype": "float32", "shape": (num_joints,)},
        "action": {"dtype": "float32", "shape": (num_joints,)},
    }
    for i in range(num_cameras):
        features[f"observation.images.cam{i}"] = {
            "dtype": "video",
            "shape": (480, 640, 3),
        }

    dataset = LeRobotDataset.create(
        repo_id=config.get("hugging_face_repo","SashoPepi")+"/"+config.get("dataset_name","franka-gello"),
        fps=config.get("fps",30),
        robot_type=robot.get("name","fr3"),
        features=features
    )

    start_episode = config.get("start_episode",0)
    end_episode = config.get("end_episode",0)
    joint_cols = [f"joint{i+1}" for i in range(num_joints)]
    action_cols = [f"action{i+1}" for i in range(num_joints)]
    
    for ep in range(start_episode,end_episode+1):
        path = os.path.join(directory_path,f"joints/episode{ep:04d}_joints.parquet")
        valid = True
        df = pd.read_parquet(path)
        states = df[joint_cols].values
        actions = df[action_cols].values
        description = df['episode_descr'][0]
        cameras = [cv2.VideoCapture(os.path.join(directory_path,f"images/episode{ep:04d}_cam{j:04d}_video.mp4")) for j in range(num_cameras)]
        for state, action in zip(states,actions):
            frames = []
            for camera in cameras:
                ret, frame = camera.read()
                if not ret:
                    print(f"Couldn't read frame")
                    valid = False
                    break 
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame)
            if not valid:
                break
            
            frame_dict = {
                "observation.state": torch.tensor(state, dtype=torch.float32),
                "action": torch.tensor(action, dtype=torch.float32),
                "task": description,
            }

            for i in range(num_cameras):
                frame_dict[f"observation.images.cam{i}"] = torch.from_numpy(frames[i])

            dataset.add_frame(frame_dict)
        dataset.save_episode()
        for camera in cameras:
            camera.release()
    dataset.finalize()
    dataset.push_to_hub() 
    del dataset

if __name__ == "__main__":
    main()