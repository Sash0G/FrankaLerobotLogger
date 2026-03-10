from robot_inference.core.observation import RobotObservation
import numpy as np
import av
from examples.diffusion.diffusion import LerobotDiffusionPolicy, LerobotDiffusionPolicyConfig


def read_frame_at_index(video_path: str, frame_index: int) -> np.ndarray:
    with av.open(video_path) as container:
        stream = container.streams.video[0]
        for i, frame in enumerate(container.decode(stream)):
            if i == frame_index:
                return frame.to_ndarray(format="rgb24")
    raise IndexError(f"Frame {frame_index} not found in {video_path}")


video_array = read_frame_at_index(
    '/home/aleksandar_georgiev/work/robot-inference-api/franka-gello-close-box/videos/observation.images.cam0/chunk-000/file-000.mp4',
    175,
)

video_array2 = read_frame_at_index(
    '/home/aleksandar_georgiev/work/robot-inference-api/franka-gello-close-box/videos/observation.images.cam1/chunk-000/file-000.mp4',
    175,
)

observation = RobotObservation(
    eef_pose=np.ones((4, 4), dtype=np.float32),
    eef_pose_from_target=np.ones((4, 4), dtype=np.float32),
    timestamps=np.array([0.0], dtype=np.float64),
    images={"cam0": video_array,"cam1": video_array2},
    gripper_state=np.array([0.8641358613967896], dtype=np.float32),
    joints=np.array([0.2390511929988861,0.1380229890346527,-0.29188305139541626,-1.569190502166748,0.04479985311627388,2.0353267192840576,-0.09232697635889053], dtype=np.float32),
)

config: LerobotDiffusionPolicyConfig = LerobotDiffusionPolicyConfig()
policy = LerobotDiffusionPolicy(config)
action = policy.predict_action(observation, "close the box")
print(action.arm_action.angles,action.gripper_action)