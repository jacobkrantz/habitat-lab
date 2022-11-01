#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import os

import numpy as np

import habitat
from habitat.core.utils import try_cv2_import
from habitat.tasks.nav.shortest_path_follower import ShortestPathFollower
from habitat.utils.visualizations import maps
from habitat.utils.visualizations.utils import images_to_video

cv2 = try_cv2_import()

IMAGE_DIR = os.path.join("examples", "images", "instance_imagenav_example2")
os.makedirs(IMAGE_DIR, exist_ok=True)


class SimpleRLEnv(habitat.RLEnv):
    def get_reward_range(self):
        return [-1, 1]

    def get_reward(self, observations):
        return 0

    def get_done(self, observations):
        return self.habitat_env.episode_over

    def get_info(self, observations):
        return self.habitat_env.get_metrics()


def make_frame(obs, info):
    def draw_top_down_map(info, output_size):
        m = maps.colorize_draw_agent_and_fit_to_height(
            info["top_down_map"], output_size
        )
        H, W, _ = m.shape
        if W > H:
            m = np.rot90(m)
            m = cv2.resize(m, (int(H / W * H), H))

        return m

    def pad_to_width(im, width):
        assert im.shape[0] < width
        assert (width - im.shape[1]) % 2 == 0

        side_bar_w = int((width - im.shape[1]) / 2)
        side_bar = np.ones((im.shape[0], side_bar_w, 3)) * 255
        return np.concatenate([side_bar, im, side_bar], axis=1)

    def write_text(im, txt):
        lt = cv2.LINE_AA
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontsize = 1.2
        white = (255, 255, 255)
        black = (0, 0, 0)

        textsize = cv2.getTextSize(txt, font, fontsize, 2)[0]
        textX = int((im.shape[1] - textsize[0]) / 2)

        im = cv2.putText(im, txt, (textX, 50), font, fontsize, black, 5, lt)
        im = cv2.putText(im, txt, (textX, 50), font, fontsize, white, 2, lt)
        return im

    depth_im = (obs["depth"] * 255).astype(np.uint8)
    depth_im = cv2.applyColorMap(depth_im, cv2.COLORMAP_VIRIDIS)
    depth_im = write_text(depth_im, "Depth")
    rgb_im = write_text(obs["rgb"].copy(), "RGB")
    left_im = np.concatenate([rgb_im, depth_im], axis=0)

    goal_im = cv2.resize(
        obs["instance_imagegoal"], (depth_im.shape[0], depth_im.shape[0])
    )
    goal_im = pad_to_width(goal_im, depth_im.shape[1])
    goal_im = write_text(goal_im, "Instance ImageGoal")
    top_down_map = draw_top_down_map(info, depth_im.shape[0])
    top_down_map = pad_to_width(top_down_map, depth_im.shape[1])
    right_im = np.concatenate((top_down_map, goal_im), axis=0)

    return np.concatenate([left_im, right_im], axis=1).astype(np.uint8)


def example():
    config = habitat.get_config("configs/tasks/instance_imagenav_hm3d.yaml")
    config.defrost()
    config.TASK.MEASUREMENTS.append("TOP_DOWN_MAP")
    config.DATASET.SPLIT = "minival"
    config.freeze()

    with SimpleRLEnv(config=config) as env:
        goal_radius = env.episodes[0].goals[0].radius
        if goal_radius is None:
            goal_radius = config.SIMULATOR.FORWARD_STEP_SIZE
        follower = ShortestPathFollower(
            env.habitat_env.sim, goal_radius, False
        )

        for episode in range(10):
            obs = env.reset()

            images = []
            while not env.habitat_env.episode_over:
                best_action = follower.get_next_action(
                    env.habitat_env.current_episode.goals[0].position
                )
                if best_action is None:
                    break

                obs, _, _, info = env.step(best_action)
                images.append(make_frame(obs, info))
            images_to_video(images, IMAGE_DIR, "%02d" % episode)


if __name__ == "__main__":
    example()
