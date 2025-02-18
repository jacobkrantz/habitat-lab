#!/usr/bin/env python3

# Copyright (c) Meta Platforms, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from typing import Optional

import magnum as mn
import numpy as np
from gym import spaces

import habitat_sim
from habitat.core.embodied_task import SimulatorTaskAction
from habitat.core.registry import registry
from habitat.sims.habitat_simulator.actions import HabitatSimActions
from habitat.tasks.rearrange.actions.articulated_agent_action import (
    ArticulatedAgentAction,
)

# flake8: noqa
# These actions need to be imported since there is a Python evaluation
# statement which dynamically creates the desired grip controller.
from habitat.tasks.rearrange.actions.grip_actions import (
    GripSimulatorTaskAction,
    MagicGraspAction,
    SuctionGraspAction,
)
from habitat.tasks.rearrange.rearrange_sim import RearrangeSim
from habitat.tasks.rearrange.utils import rearrange_collision, rearrange_logger


@registry.register_task_action
class EmptyAction(ArticulatedAgentAction):
    """A No-op action useful for testing and in some controllers where we want
    to wait before the next operation.
    """

    @property
    def action_space(self):
        return spaces.Dict(
            {
                "empty_action": spaces.Box(
                    shape=(1,),
                    low=-1,
                    high=1,
                    dtype=np.float32,
                )
            }
        )

    def step(self, *args, **kwargs):
        return self._sim.step(HabitatSimActions.empty)


@registry.register_task_action
class RearrangeStopAction(SimulatorTaskAction):
    def reset(self, *args, **kwargs):
        super().reset(*args, **kwargs)
        self.does_want_terminate = False

    def step(self, task, *args, is_last_action, **kwargs):
        should_stop = kwargs.get("rearrange_stop", [1.0])
        if should_stop[0] > 0.0:
            rearrange_logger.debug(
                "Rearrange stop action requesting episode stop."
            )
            self.does_want_terminate = True

        if is_last_action:
            return self._sim.step(HabitatSimActions.rearrange_stop)
        else:
            return {}


@registry.register_task_action
class ArmAction(ArticulatedAgentAction):
    """An arm control and grip control into one action space."""

    def __init__(self, *args, config, sim: RearrangeSim, **kwargs):
        super().__init__(*args, config=config, sim=sim, **kwargs)
        arm_controller_cls = eval(self._config.arm_controller)
        self._sim: RearrangeSim = sim
        self.arm_ctrlr = arm_controller_cls(
            *args, config=config, sim=sim, **kwargs
        )

        if self._config.grip_controller is not None:
            grip_controller_cls = eval(self._config.grip_controller)
            self.grip_ctrlr: Optional[
                GripSimulatorTaskAction
            ] = grip_controller_cls(*args, config=config, sim=sim, **kwargs)
        else:
            self.grip_ctrlr = None

        self.disable_grip = False
        if "disable_grip" in config:
            self.disable_grip = config["disable_grip"]

    def reset(self, *args, **kwargs):
        self.arm_ctrlr.reset(*args, **kwargs)
        if self.grip_ctrlr is not None:
            self.grip_ctrlr.reset(*args, **kwargs)

    @property
    def action_space(self):
        action_spaces = {
            self._action_arg_prefix
            + "arm_action": self.arm_ctrlr.action_space,
        }
        if self.grip_ctrlr is not None and self.grip_ctrlr.requires_action:
            action_spaces[
                self._action_arg_prefix + "grip_action"
            ] = self.grip_ctrlr.action_space
        return spaces.Dict(action_spaces)

    def step(self, is_last_action, *args, **kwargs):
        arm_action = kwargs[self._action_arg_prefix + "arm_action"]
        self.arm_ctrlr.step(arm_action)
        if self.grip_ctrlr is not None and not self.disable_grip:
            grip_action = kwargs[self._action_arg_prefix + "grip_action"]
            self.grip_ctrlr.step(grip_action)
        if is_last_action:
            return self._sim.step(HabitatSimActions.arm_action)
        else:
            return {}


@registry.register_task_action
class ArmRelPosAction(ArticulatedAgentAction):
    """
    The arm motor targets are offset by the delta joint values specified by the
    action
    """

    def __init__(self, *args, config, sim: RearrangeSim, **kwargs):
        super().__init__(*args, config=config, sim=sim, **kwargs)
        self._delta_pos_limit = self._config.delta_pos_limit

    @property
    def action_space(self):
        return spaces.Box(
            shape=(self._config.arm_joint_dimensionality,),
            low=-1,
            high=1,
            dtype=np.float32,
        )

    def step(self, delta_pos, should_step=True, *args, **kwargs):
        # clip from -1 to 1
        delta_pos = np.clip(delta_pos, -1, 1)
        delta_pos *= self._delta_pos_limit

        # The actual joint positions
        self._sim: RearrangeSim
        self.cur_articulated_agent.arm_motor_pos = (
            delta_pos + self.cur_articulated_agent.arm_motor_pos
        )


@registry.register_task_action
class ArmRelPosMaskAction(ArticulatedAgentAction):
    """
    The arm motor targets are offset by the delta joint values specified by the
    action
    """

    def __init__(self, *args, config, sim: RearrangeSim, **kwargs):
        super().__init__(*args, config=config, sim=sim, **kwargs)
        self._delta_pos_limit = self._config.delta_pos_limit
        self._arm_joint_mask = self._config.arm_joint_mask

    @property
    def action_space(self):
        return spaces.Box(
            shape=(self._config.arm_joint_dimensionality,),
            low=-1,
            high=1,
            dtype=np.float32,
        )

    def step(self, delta_pos, should_step=True, *args, **kwargs):
        # clip from -1 to 1
        delta_pos = np.clip(delta_pos, -1, 1)
        delta_pos *= self._delta_pos_limit

        mask_delta_pos = np.zeros(len(self._arm_joint_mask))
        src_idx = 0
        tgt_idx = 0
        for mask in self._arm_joint_mask:
            if mask == 0:
                tgt_idx += 1
                src_idx += 1
                continue
            mask_delta_pos[tgt_idx] = delta_pos[src_idx]
            tgt_idx += 1
            src_idx += 1

        # Although habitat_sim will prevent the motor from exceeding limits,
        # clip the motor joints first here to prevent the arm from being unstable.
        min_limit, max_limit = self.cur_articulated_agent.arm_joint_limits
        target_arm_pos = (
            mask_delta_pos + self.cur_articulated_agent.arm_motor_pos
        )
        set_arm_pos = np.clip(target_arm_pos, min_limit, max_limit)

        # The actual joint positions
        self._sim: RearrangeSim
        self.cur_articulated_agent.arm_motor_pos = set_arm_pos


@registry.register_task_action
class ArmRelPosKinematicAction(ArticulatedAgentAction):
    """
    The arm motor targets are offset by the delta joint values specified by the
    action
    """

    def __init__(self, *args, config, sim: RearrangeSim, **kwargs):
        super().__init__(*args, config=config, sim=sim, **kwargs)
        self._delta_pos_limit = self._config.delta_pos_limit
        self._should_clip = self._config.get("should_clip", True)

    @property
    def action_space(self):
        return spaces.Box(
            shape=(self._config.arm_joint_dimensionality,),
            low=0,
            high=1,
            dtype=np.float32,
        )

    def step(self, delta_pos, *args, **kwargs):
        if self._should_clip:
            # clip from -1 to 1
            delta_pos = np.clip(delta_pos, -1, 1)
        delta_pos *= self._delta_pos_limit
        self._sim: RearrangeSim

        set_arm_pos = delta_pos + self.cur_articulated_agent.arm_joint_pos
        self.cur_articulated_agent.arm_joint_pos = set_arm_pos
        self.cur_articulated_agent.fix_joint_values = set_arm_pos


@registry.register_task_action
class ArmAbsPosAction(ArticulatedAgentAction):
    """
    The arm motor targets are directly set to the joint configuration specified
    by the action.
    """

    @property
    def action_space(self):
        return spaces.Box(
            shape=(self._config.arm_joint_dimensionality,),
            low=0,
            high=1,
            dtype=np.float32,
        )

    def step(self, set_pos, *args, **kwargs):
        # No clipping because the arm is being set to exactly where it needs to
        # go.
        self._sim: RearrangeSim
        self.cur_articulated_agent.arm_motor_pos = set_pos


@registry.register_task_action
class ArmAbsPosKinematicAction(ArticulatedAgentAction):
    """
    The arm is kinematically directly set to the joint configuration specified
    by the action.
    """

    @property
    def action_space(self):
        return spaces.Box(
            shape=(self._config.arm_joint_dimensionality,),
            low=0,
            high=1,
            dtype=np.float32,
        )

    def step(self, set_pos, *args, **kwargs):
        # No clipping because the arm is being set to exactly where it needs to
        # go.
        self._sim: RearrangeSim
        self.cur_articulated_agent.arm_joint_pos = set_pos


@registry.register_task_action
class ArmRelPosKinematicReducedActionStretch(ArticulatedAgentAction):
    """
    The arm motor targets are offset by the delta joint values specified by the
    action and the mask. This function is used for Stretch.
    """

    def __init__(self, *args, config, sim: RearrangeSim, **kwargs):
        super().__init__(*args, config=config, sim=sim, **kwargs)
        self.last_arm_action = None
        self._delta_pos_limit = self._config.delta_pos_limit
        self._should_clip = self._config.get("should_clip", True)
        self._arm_joint_mask = self._config.arm_joint_mask

    def reset(self, *args, **kwargs):
        super().reset(*args, **kwargs)
        self.last_arm_action = None

    @property
    def action_space(self):
        self.step_c = 0
        return spaces.Box(
            shape=(self._config.arm_joint_dimensionality,),
            low=-1,
            high=1,
            dtype=np.float32,
        )

    def step(self, delta_pos, *args, **kwargs):
        if self._should_clip:
            # clip from -1 to 1
            delta_pos = np.clip(delta_pos, -1, 1)
        delta_pos *= self._delta_pos_limit
        self._sim: RearrangeSim

        # Expand delta_pos based on mask
        expanded_delta_pos = np.zeros(len(self._arm_joint_mask))
        src_idx = 0
        tgt_idx = 0
        for mask in self._arm_joint_mask:
            if mask == 0:
                tgt_idx += 1
                src_idx += 1
                continue
            expanded_delta_pos[tgt_idx] = delta_pos[src_idx]
            tgt_idx += 1
            src_idx += 1

        min_limit, max_limit = self.cur_articulated_agent.arm_joint_limits
        set_arm_pos = (
            expanded_delta_pos + self.cur_articulated_agent.arm_motor_pos
        )
        # Perform roll over to the joints so that the user cannot control
        # the motor 2, 3, 4 for the arm.
        if expanded_delta_pos[0] >= 0:
            for i in range(3):
                if set_arm_pos[i] > max_limit[i]:
                    set_arm_pos[i + 1] += set_arm_pos[i] - max_limit[i]
                    set_arm_pos[i] = max_limit[i]
        else:
            for i in range(3):
                if set_arm_pos[i] < min_limit[i]:
                    set_arm_pos[i + 1] -= min_limit[i] - set_arm_pos[i]
                    set_arm_pos[i] = min_limit[i]
        set_arm_pos = np.clip(set_arm_pos, min_limit, max_limit)

        self.cur_articulated_agent.arm_motor_pos = set_arm_pos


@registry.register_task_action
class BaseVelAction(ArticulatedAgentAction):
    """
    The articulated agent base motion is constrained to the NavMesh and controlled with velocity commands integrated with the VelocityControl interface.

    Optionally cull states with active collisions if config parameter `allow_dyn_slide` is True
    """

    def __init__(self, *args, config, sim: RearrangeSim, **kwargs):
        super().__init__(*args, config=config, sim=sim, **kwargs)
        self._sim: RearrangeSim = sim
        self.base_vel_ctrl = habitat_sim.physics.VelocityControl()
        self.base_vel_ctrl.controlling_lin_vel = True
        self.base_vel_ctrl.lin_vel_is_local = True
        self.base_vel_ctrl.controlling_ang_vel = True
        self.base_vel_ctrl.ang_vel_is_local = True
        self._allow_dyn_slide = self._config.get("allow_dyn_slide", True)
        self._lin_speed = self._config.lin_speed
        self._ang_speed = self._config.ang_speed
        self._allow_back = self._config.allow_back

    @property
    def action_space(self):
        lim = 20
        return spaces.Dict(
            {
                self._action_arg_prefix
                + "base_vel": spaces.Box(
                    shape=(2,), low=-lim, high=lim, dtype=np.float32
                )
            }
        )

    def _capture_articulated_agent_state(self):
        return {
            "forces": self.cur_articulated_agent.sim_obj.joint_forces,
            "vel": self.cur_articulated_agent.sim_obj.joint_velocities,
            "pos": self.cur_articulated_agent.sim_obj.joint_positions,
        }

    def _set_articulated_agent_state(self, set_dat):
        self.cur_articulated_agent.sim_obj.joint_positions = set_dat["forces"]
        self.cur_articulated_agent.sim_obj.joint_velocities = set_dat["vel"]
        self.cur_articulated_agent.sim_obj.joint_forces = set_dat["pos"]

    def update_base(self):
        ctrl_freq = self._sim.ctrl_freq

        before_trans_state = self._capture_articulated_agent_state()

        trans = self.cur_articulated_agent.sim_obj.transformation
        rigid_state = habitat_sim.RigidState(
            mn.Quaternion.from_matrix(trans.rotation()), trans.translation
        )

        target_rigid_state = self.base_vel_ctrl.integrate_transform(
            1 / ctrl_freq, rigid_state
        )
        end_pos = self._sim.step_filter(
            rigid_state.translation, target_rigid_state.translation
        )

        # Offset the base
        end_pos -= self.cur_articulated_agent.params.base_offset

        target_trans = mn.Matrix4.from_(
            target_rigid_state.rotation.to_matrix(), end_pos
        )
        self.cur_articulated_agent.sim_obj.transformation = target_trans

        if not self._allow_dyn_slide:
            # Check if in the new articulated_agent state the arm collides with anything.
            # If so we have to revert back to the previous transform
            self._sim.internal_step(-1)
            colls = self._sim.get_collisions()
            did_coll, _ = rearrange_collision(
                colls, self._sim.snapped_obj_id, False
            )
            if did_coll:
                # Don't allow the step, revert back.
                self._set_articulated_agent_state(before_trans_state)
                self.cur_articulated_agent.sim_obj.transformation = trans
        if self.cur_grasp_mgr.snap_idx is not None:
            # Holding onto an object, also kinematically update the object.
            # object.
            self.cur_grasp_mgr.update_object_to_grasp()

        if self.cur_articulated_agent._base_type == "leg":
            # Fix the leg joints
            self.cur_articulated_agent.leg_joint_pos = (
                self.cur_articulated_agent.params.leg_init_params
            )

    def step(self, *args, is_last_action, **kwargs):
        lin_vel, ang_vel = kwargs[self._action_arg_prefix + "base_vel"]
        lin_vel = np.clip(lin_vel, -1, 1) * self._lin_speed
        ang_vel = np.clip(ang_vel, -1, 1) * self._ang_speed
        if not self._allow_back:
            lin_vel = np.maximum(lin_vel, 0)

        self.base_vel_ctrl.linear_velocity = mn.Vector3(lin_vel, 0, 0)
        self.base_vel_ctrl.angular_velocity = mn.Vector3(0, ang_vel, 0)

        if lin_vel != 0.0 or ang_vel != 0.0:
            self.update_base()

        if is_last_action:
            return self._sim.step(HabitatSimActions.base_velocity)
        else:
            return {}


@registry.register_task_action
class ArmEEAction(ArticulatedAgentAction):
    """Uses inverse kinematics (requires pybullet) to apply end-effector position control for the articulated_agent's arm."""

    def __init__(self, *args, sim: RearrangeSim, **kwargs):
        self.ee_target: Optional[np.ndarray] = None
        self.ee_index: Optional[int] = 0
        super().__init__(*args, sim=sim, **kwargs)
        self._sim: RearrangeSim = sim
        self._render_ee_target = self._config.get("render_ee_target", False)
        self._ee_ctrl_lim = self._config.ee_ctrl_lim

    def reset(self, *args, **kwargs):
        super().reset()
        cur_ee = self._ik_helper.calc_fk(
            np.array(self._sim.articulated_agent.arm_joint_pos)
        )

        self.ee_target = cur_ee

    @property
    def action_space(self):
        return spaces.Box(shape=(3,), low=-1, high=1, dtype=np.float32)

    def apply_ee_constraints(self):
        self.ee_target = np.clip(
            self.ee_target,
            self._sim.articulated_agent.params.ee_constraint[
                self.ee_index, :, 0
            ],
            self._sim.articulated_agent.params.ee_constraint[
                self.ee_index, :, 1
            ],
        )

    def set_desired_ee_pos(self, ee_pos: np.ndarray) -> None:
        self.ee_target += np.array(ee_pos)

        self.apply_ee_constraints()

        joint_pos = np.array(self._sim.articulated_agent.arm_joint_pos)
        joint_vel = np.zeros(joint_pos.shape)

        self._ik_helper.set_arm_state(joint_pos, joint_vel)

        des_joint_pos = self._ik_helper.calc_ik(self.ee_target)
        des_joint_pos = list(des_joint_pos)
        self._sim.articulated_agent.arm_motor_pos = des_joint_pos

    def step(self, ee_pos, **kwargs):
        ee_pos = np.clip(ee_pos, -1, 1)
        ee_pos *= self._ee_ctrl_lim
        self.set_desired_ee_pos(ee_pos)

        if self._render_ee_target:
            global_pos = self._sim.articulated_agent.base_transformation.transform_point(
                self.ee_target
            )
            self._sim.viz_ids["ee_target"] = self._sim.visualize_position(
                global_pos, self._sim.viz_ids["ee_target"]
            )


@registry.register_task_action
class HumanoidJointAction(ArticulatedAgentAction):
    def __init__(self, *args, sim: RearrangeSim, **kwargs):
        super().__init__(*args, sim=sim, **kwargs)
        self._sim: RearrangeSim = sim
        self.num_joints = self._config.num_joints

    def reset(self, *args, **kwargs):
        super().reset()

    @property
    def action_space(self):
        num_joints = self.num_joints
        num_dim_transform = 16
        # The action space is the number of joints plus 16 for a 4x4 transformtion matrix for the base
        return spaces.Dict(
            {
                "human_joints_trans": spaces.Box(
                    shape=(4 * num_joints + num_dim_transform,),
                    low=-1,
                    high=1,
                    dtype=np.float32,
                )
            }
        )

    def step(self, human_joints_trans, is_last_action, **kwargs):
        r"""
        Updates the joint rotations and root transformation of the humanoid.
        :param human_joint_trans: Array of size (num_joints*4)+16. The last 16
            dimensions define the 4x4 root transformation matrix, the first elements
            correspond to a flattened list of quaternions for each joint. When the array is all 0
            it keeps the previous joint rotation and transform.
        :param is_last_action: whether this is the last action before calling environment
          step
        """
        new_joints = human_joints_trans[:-16]
        new_pos_transform = human_joints_trans[-16:]

        # When the array is all 0, this indicates we are not setting
        # the human joint
        if np.array(new_pos_transform).sum() != 0:
            vecs = [
                mn.Vector4(new_pos_transform[i * 4 : (i + 1) * 4])
                for i in range(4)
            ]
            new_transform = mn.Matrix4(*vecs)
            self.cur_articulated_agent.set_joint_transform(
                new_joints, new_transform
            )

        if is_last_action:
            return self._sim.step(HabitatSimActions.humanoidjoint_action)
        else:
            return {}
