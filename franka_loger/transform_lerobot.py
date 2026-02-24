from lerobot.datasets.lerobot_dataset import LeRobotDataset
import torch
import pandas as pd
import cv2

def main():
    dataset = LeRobotDataset.create(
        repo_id="Sash0g/franka-gello",
        fps=2,
        robot_type="franka",
        features={
            "observation.state": {"dtype": "float32", "shape": (7,)},
            "action": {"dtype": "float32", "shape": (7,)},
            "observation.images.wrist": {"dtype": "video", "shape": (480, 640, 3)},
            "observation.images.side": {"dtype": "video", "shape": (480, 640, 3)},
        }
    )
    episode_states = []
    episode_actions = []
    episode_video = []
    descriptions = []
    episodes_count = int(input("Number of episodes:"))

    for i in range(0,episodes_count):
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
            for i in range(1): #Change to 2 for 2 cameras!!!
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