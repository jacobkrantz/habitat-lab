import os

import numpy as np

import habitat
from habitat.core.utils import try_cv2_import
from habitat.config.read_write import read_write
from habitat.tasks.nav.shortest_path_follower import ShortestPathFollower
from habitat.utils.visualizations import maps
from habitat.utils.visualizations.utils import images_to_video
from omegaconf import OmegaConf

cv2 = try_cv2_import()


IS_OBJECTNAV = True

IMAGE_DIR = os.path.join("examples", "images")
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)


class SimpleRLEnv(habitat.RLEnv):
    def get_reward_range(self):
        return [-1, 1]

    def get_reward(self, observations):
        return 0

    def get_done(self, observations):
        return self.habitat_env.episode_over

    def get_info(self, observations):
        return self.habitat_env.get_metrics()


def draw_top_down_map(info, output_size):
    return maps.colorize_draw_agent_and_fit_to_height(
        info["top_down_map"], output_size
    )


def write_on_img(img, text, mode=1):
    h, w, c = img.shape
    font_thickness = 1
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_size = 0.8

    textsize = cv2.getTextSize(text, font, font_size, font_thickness)[0]
    x = int((w - textsize[0]) / 2) if mode == 1 else 10
    y = int((h + textsize[1]) / 2)

    cv2.putText(
        img,
        text,
        (x, y),
        font,
        font_size,
        (0, 0, 0),
        font_thickness,
        lineType=cv2.LINE_AA,
    )

    return np.clip(img, 0, 255)


def make_compass(theta=0, r=200, r2=25):
    """
    r: radius of main circle. Overall image will be a square of 2r x 2r.
    r2: radius of heading indicator.
    theta: angle in radians
    """
    x = 255 * np.ones((r*2, r*2, 3), dtype=np.uint8)
    center = np.array([r, r])

    black = [0,0,0]
    gray = [150, 142, 141]
    cv2.circle(x, center, r, gray, -1)

    look_at_center = np.array([0,-(r-r2)])

    theta = -theta
    rot = np.array(
        [
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ]
    )
    look_at_center = np.dot(rot, look_at_center).astype(int)
    look_at_center = center+look_at_center
    cv2.circle(x, look_at_center, r2, black, -1)
    cv2.line(x, center, look_at_center, black, thickness=12)

    return x


def write_action(best_action, frame):

    # add velocity controls
    if best_action == 0: # STOP
        lin = 0.0
        ang = 0.0
    elif best_action == 1:  # FWD
        lin = 0.25
        ang = 0.0
    elif best_action == 2:  # TURN LEFT
        lin = 0.0
        ang = 0.52
    elif best_action == 3:
        lin = 0.0
        ang = -0.52

    text = f"Linear Vel: {lin} m/s"
    hbar1 = 255 * np.ones((50, frame.shape[1], 3), dtype=frame.dtype)
    hbar1 = write_on_img(hbar1, text, mode=2)

    text = f"Angular Vel: {ang} rad/s"
    hbar2 = 255 * np.ones((50, frame.shape[1], 3), dtype=frame.dtype)
    hbar2 = write_on_img(hbar2, text, mode=2)
    return np.concatenate([hbar1, hbar2], axis=0)

def make_frame(obs, info, best_action):
    rgb = obs["rgb"]
    depth = obs["depth"]
    depth = 255 * np.concatenate((depth, depth, depth), axis=2)
    depth = depth.astype(rgb.dtype)

    h = rgb.shape[0]
    top_down_map = draw_top_down_map(info, h)

    vbar = 255 * np.ones((h, 20, 3), dtype=rgb.dtype)

    if IS_OBJECTNAV:
        to_cat = [rgb, vbar, depth, vbar, top_down_map]
    else:
        goal = cv2.resize(obs["instance_imagegoal"], (h, h))
        # cv2.imwrite("goal_img.png", cv2.cvtColor(obs["instance_imagegoal"], cv2.COLOR_RGB2BGR))
        to_cat = [goal, vbar, rgb, vbar, depth, vbar, top_down_map]

    frame = np.concatenate(to_cat, axis=1)

    hbar = 255 * np.ones((50, frame.shape[1], 3), dtype=rgb.dtype)
    x = str(round(obs["gps"][0], 2))
    z = str(round(obs["gps"][1], 2))
    hbar = write_on_img(hbar, f"x={x}, z={z}")
    frame = np.concatenate([hbar, frame], axis=0)

    compass_img = make_compass(theta=obs["compass"][0])
    pad_h = compass_img.shape[0]
    pad_w = frame.shape[1] - compass_img.shape[1]
    padding = 255 * np.ones((pad_h, pad_w, 3), dtype=rgb.dtype)
    compass_img = np.concatenate((compass_img, padding), axis=1)
    frame = np.concatenate([compass_img, frame], axis=0)

    frame = np.concatenate([write_action(best_action, frame), frame], axis=0)

    return frame


def shortest_path_example():
    if IS_OBJECTNAV:
        cfg_path = "benchmark/nav/objectnav/objectnav_v2_hm3d_stretch.yaml"
    else:
        cfg_path = "benchmark/nav/instance_imagenav/instance_imagenav_hm3d_v3.yaml"

    config = habitat.get_config(
        config_path=cfg_path,
        overrides=[
            "+habitat/task/measurements@habitat.task.measurements.top_down_map=top_down_map",
        ],
    )

    with read_write(config):
        config.habitat.task.measurements.top_down_map.fog_of_war.fov = 42
        config.habitat.simulator.turn_angle = 30

    with SimpleRLEnv(config=config) as env:
        if IS_OBJECTNAV:
            env.episodes = [
                ep
                for ep in env.episodes
                if ep.scene_id.split("/")[-2] == "00827-BAbdmeyTvMZ" and ep.object_category == "chair"
            ]
            env.episodes = [env.episodes[3]]  # 6 total
        else:
            env.episodes = [e for e in env.episodes if int(e.episode_id) == 119]

        goal_radius = env.episodes[0].goals[0].radius
        if goal_radius is None:
            goal_radius = config.habitat.simulator.forward_step_size
        follower = ShortestPathFollower(
            env.habitat_env.sim, goal_radius, False
        )

        for episode in range(50):
            observations = env.reset()

            images = []

            if IS_OBJECTNAV:
                g_idx = np.argmin(
                    [
                        env.habitat_env.sim.geodesic_distance(
                            env.episodes[0].start_position, g.position
                        )
                        for g in env.habitat_env.current_episode.goals
                    ]
                )
                g = env.habitat_env.current_episode.goals[g_idx]
            else:
                g = env.habitat_env.current_episode.goals[0]

            while not env.habitat_env.episode_over:
                best_action = follower.get_next_action(g.position)
                if best_action is None:
                    break

                observations, _, _, info = env.step(best_action)
                images.append(make_frame(observations, info, best_action))

            name = f"trajectory_objectnav_{episode}" if IS_OBJECTNAV else f"trajectory_{episode}"
            images_to_video(images, "./", name, fps=8)
            print(f"Episode {episode} finished")
            quit()


def main():
    shortest_path_example()


if __name__ == "__main__":
    main()
