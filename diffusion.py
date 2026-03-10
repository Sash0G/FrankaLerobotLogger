import dataclasses
from queue import deque
from typing import Deque, Dict, List
from lerobot.policies.diffusion.modeling_diffusion import DiffusionPolicy
from lerobot.policies.utils import prepare_observation_for_inference
from lerobot.policies.factory import  make_pre_post_processors
import numpy as np
import numpy.typing as npt
from contextlib import nullcontext
from databib.config import Config, Configurable
import torch
from robot_inference.core.action import (
    JointAnglesAction,
    JointVelocitiesAction,
    RobotAction,
    ArmAction
)
from robot_inference.core.observation import RobotObservation

class LerobotDiffusionPolicyConfig(Config):
    checkpoint_path: str = "/home/aleksandar_georgiev/work/robot-inference-api/first_policy/"
    action_space: str = "joint_positions"

    def __post_init__(self):
        super().__post_init__()
        assert self.action_space in ["joint_velocities", "joint_positions"], "Invalid action space specified!"


class LerobotDiffusionPolicy(Configurable[LerobotDiffusionPolicyConfig]):
    def __init__(self, config: LerobotDiffusionPolicyConfig):
        super().__init__(config)

        self.device = torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")
        self.policy = DiffusionPolicy.from_pretrained(config.checkpoint_path).to(self.device)
        self.policy.eval()
        self.preprocessor, self.postprocessor = make_pre_post_processors(
                policy_cfg=self.policy,
                pretrained_path=config.checkpoint_path,
            )

    def predict_action(
        self,
        observation: RobotObservation,
        instruction: str,
    ) -> RobotAction | List[RobotAction]:

        state = np.concatenate([observation.joints, observation.gripper_state]).astype(np.float32)
        observation_convert = {
            "observation.state": state
        }
        for camera in observation.images:
            img = observation.images[camera].astype(np.float32)
            observation_convert[f"observation.images.{camera}"] = img
            print(img.shape)

        with (
            torch.inference_mode(),
            torch.autocast(device_type=self.device.type) if self.device.type == "cuda" else nullcontext(),
        ):
            observation_convert = prepare_observation_for_inference(observation_convert, self.device, instruction)
            observation_convert = self.preprocessor(observation_convert)
            action = self.policy.select_action(observation_convert)
            action = self.postprocessor(action)

        arm_action: ArmAction = ArmAction.from_dict({'type': 'joint_angles', 'angles': action[0][:7].cpu().numpy()})
        action_convert: RobotAction = RobotAction(gripper_action=action[0][7], arm_action=arm_action)

        return action_convert


    def reset(self) -> None:
        self._current_action_chunk = deque()
