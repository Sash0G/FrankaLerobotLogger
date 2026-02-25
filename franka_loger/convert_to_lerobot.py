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
        required=True,
        type=str,
        help="Name of config file"
    )

    args = parser.parse_args()
    package_share_directory = get_package_share_directory('franka_loger')
    config_file_path = os.path.join(package_share_directory, 'config', args.config)

    with open(config_file_path, "r") as f:
        config = yaml.safe_load(f)

    print(config)
    robot = config.get("robot",{})
    num_joints = robot.get("num_joints",7)
    num_cameras = robot.get("num_cameras",2)
    dataset = LeRobotDataset.create(
        repo_id=config.get("hugging_face_repo","SashoPepi")+"/"+config.get("dataset_name","franka-gello"),
        fps=config.get("fps",30),
        robot_type=robot.get("name","fr3"),
        features={
            "observation.state": {"dtype": "float32", "shape": (num_joints,)},
            "action": {"dtype": "float32", "shape": (num_joints,)},
            "observation.images.wrist": {"dtype": "video", "shape": (480, 640, 3)},
            "observation.images.side": {"dtype": "video", "shape": (480, 640, 3)},
        }
    )
    episode_states = []
    episode_actions = []
    episode_video = []
    descriptions = []

    start_episode = config.get("start_episode",0)
    end_episode = config.get("end_episode",0)


    for i in range(start_episode,end_episode+1):
        df = pd.read_parquet(f"./joints/episode{i:04d}_joints.parquet")
        episode_states.append(df[["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "joint7"]].values)
        episode_actions.append(df[["action1", "action2", "action3", "action4", "action5", "action6", "action7"]].values)
        descriptions.append(df['episode_descr'])
        cameras = []
        for  j in range(2):
            cameras.append(cv2.VideoCapture(f"./images/episode{i:04d}_cam{j:04d}_video.mp4"))
        episode_video.append(cameras)

    for states, actions, description, video in zip(episode_states,episode_actions,descriptions,episode_video):
        for state, action in zip(states,actions):
            frames = []
            for i in range(num_cameras): #Change to 2 for 2 cameras!!!
                ret, frame = video[i].read()
                if not ret:
                    print(f"Couldn't read frame")
                    frame = None 
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame) 

            dataset.add_frame({
                "observation.state": torch.tensor(state, dtype=torch.float32),
                "action":  torch.tensor(action, dtype=torch.float32),
                "observation.images.wrist": torch.from_numpy(frames[0]),
                "observation.images.side": torch.from_numpy(frames[0]), #Change to 1 for 2 cameras!!!
                "task": description[0],
            })
        dataset.save_episode()

    dataset.push_to_hub() 
    del dataset

if __name__ == "__main__":
    main()