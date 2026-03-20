import os
os.environ["SVT_LOG"] = "1"  
os.environ["IMAGEIO_FFMPEG_LOG_LEVEL"] = "error" 
os.environ["IMAGEIO_FFMPEG_EXE"] = "ffmpeg"
from lerobot.datasets.lerobot_dataset import LeRobotDataset
import torch
import pandas as pd
import yaml
import argparse
from ament_index_python.packages import get_package_share_directory

import decord
from huggingface_hub import repo_exists
import shutil
class ConvertLerobot():
    def __init__(self, config):
        self.repo_id = config.get("hugging_face_repo","SashoPepi")+"/"+config.get("dataset_name","franka-gello")
        self.root = config.get("root_path", os.getcwd())+f"/data/{self.repo_id}"
        self.robot = config.get("robot",{})
        self.num_joints = self.robot.get("num_joints",7)
        if(self.robot.get("gripper")):
            self.num_joints+=1
        self.num_cameras = self.robot.get("num_cameras",2)
        self.features = self.create_features()
        self.fps = config.get("fps",30)
        self.directory_path = config.get("directory_path","/workspace/ros2")
        self.start_episode = config.get("start_episode",0)
        self.end_episode = config.get("end_episode",0)

    def create_features(self):
        features = {
            "observation.state": {"dtype": "float32", "shape": (self.num_joints,), "names": "observation.state",},
            "action": {"dtype": "float32", "shape": (self.num_joints,), "names": "action",},
        }
        for i in range(self.num_cameras):
            features[f"observation.images.cam{i}"] = {
                "dtype": "video",
                "shape": (3, 480, 640),
                "names": f"observation.images.cam{i}",
            }
        return features

    def load_dataset(self):  
        if repo_exists(repo_id=self.repo_id, repo_type="dataset"):
            print("Dataset exists on hugging face.")
            return LeRobotDataset(repo_id=self.repo_id,root = self.root)
        else:
            if os.path.isdir(self.root):
                shutil.rmtree(self.root)
            return LeRobotDataset.create(
                repo_id=self.repo_id,
                root = self.root,
                fps=self.fps,
                robot_type=self.robot.get("name","fr3"),
                features=self.features,
                streaming_encoding=True)

    def convert_dataset(self):
        dataset = self.load_dataset()
        joint_cols = [f"joint{i+1}" for i in range(self.num_joints)]
        action_cols = [f"action{i+1}" for i in range(self.num_joints)]
        decord.bridge.set_bridge('torch')
        for ep in range(self.start_episode, self.end_episode + 1):
            
            path = os.path.join(self.directory_path, f"joints/episode{ep:04d}_joints.parquet")
            df = pd.read_parquet(path)
            states = df[joint_cols].values
            actions = df[action_cols].values
            description = df['episode_descr'][0]
            
            cam_frames = []
            for j in range(self.num_cameras):
                video_path = os.path.join(self.directory_path, f"images/episode{ep:04d}_cam{j:04d}_video.mp4")
                vr = decord.VideoReader(video_path, ctx=decord.cpu(0))
                all_frames = vr.get_batch(range(len(vr))).permute(0, 3, 1, 2)
                cam_frames.append(all_frames)
            print(f"{ep-self.start_episode}/{self.end_episode-self.start_episode}")
            for step_idx, (state, action) in enumerate(zip(states, actions)):
                
                frame_dict = {
                    "observation.state": torch.tensor(state, dtype=torch.float32),
                    "action": torch.tensor(action, dtype=torch.float32),
                    "task": description,
                }

                for i in range(self.num_cameras):
                    frame_dict[f"observation.images.cam{i}"] = cam_frames[i][step_idx]

                dataset.add_frame(frame_dict)        
            dataset.save_episode()
        dataset.finalize()
        dataset.push_to_hub() 
        del dataset

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
    
    converter = ConvertLerobot(config)
    converter.convert_dataset()

if __name__ == "__main__":
    main()