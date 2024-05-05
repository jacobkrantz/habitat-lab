import argparse
import json
import os
import traceback

import matplotlib
import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from entities import Object, Receptacle, Room, Scene
from omegaconf import OmegaConf
from tqdm import tqdm

matplotlib.use("Agg")


def load_configuration():
    """
    Load configuration from config.yaml file.
    """
    config_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "conf/config.yaml"
    )
    return OmegaConf.load(config_path)


def load_episode_data(episode_data_dir, episode_id):
    """
    Load episode data from JSON file.
    """
    with open(
        os.path.join(episode_data_dir, f"episode_{episode_id}.json")
    ) as f:
        return json.load(f)


def load_run_data(run_json, episode_id):
    """
    Load run data and retrieve episode data.
    """
    with open(run_json) as f:
        run_data = json.load(f)
    for episode in run_data["episodes"]:
        if episode["episode_id"] == str(episode_id):
            return episode
    return None


def plot_object(config, object_id, save_path=None):
    """
    Plot specific object.
    """
    object = Object(config, object_id)
    fig, ax = object.plot()
    if save_path:
        plt.savefig(save_path, dpi=400)
    else:
        plt.show()
    fig.clear()
    plt.close()
    del object


def plot_receptacle(config, receptacle_id, icon_path, save_path=None):
    """
    Plot specific receptacle.
    """
    receptacle = Receptacle(config, receptacle_id, icon_path)
    fig, ax = receptacle.plot()
    if save_path:
        plt.savefig(save_path, dpi=400)
    else:
        plt.show()
    fig.clear()
    plt.close()
    del receptacle


def plot_room(
    config, room_id, episode_data, receptacle_icon_mapping, save_path=None
):
    """
    Plot specific room.
    """
    objects = [
        Object(config, obj_id) for obj_id in episode_data["object_to_room"]
    ]
    room_receptacles = []
    for receptacle_id, r_room_id in episode_data["recep_to_room"].items():
        if r_room_id == room_id:
            icon_path = receptacle_icon_mapping.get(
                receptacle_id, "receptacles/chair@2x.png"
            )
            room_receptacles.append(
                Receptacle(config, receptacle_id, icon_path)
            )
    room_objects = [
        obj
        for obj in objects
        if episode_data["object_to_room"][obj.object_id] == room_id
    ]
    room = Room(config, room_id, room_receptacles, room_objects)
    fig, ax = room.plot()
    if save_path:
        plt.savefig(save_path, dpi=400)
    else:
        plt.show()
    fig.clear()
    plt.close()
    room.cleanup()
    del room


def plot_scene(
    config,
    episode_data,
    propositions,
    constraints,
    receptacle_icon_mapping,
    save_path=None,
):
    """
    Plot entire scene.
    """
    objects = [
        Object(config, obj_id) for obj_id in episode_data["object_to_room"]
    ]
    rooms = []
    for room_id in episode_data["rooms"]:
        room_receptacles = []
        for receptacle_id, r_room_id in episode_data["recep_to_room"].items():
            if r_room_id == room_id:
                icon_path = receptacle_icon_mapping.get(
                    receptacle_id, "receptacles/chair@2x.png"
                )
                room_receptacles.append(
                    Receptacle(config, receptacle_id, icon_path)
                )
        room_objects = [
            obj
            for obj in objects
            if episode_data["object_to_room"][obj.object_id] == room_id
        ]
        room = Room(config, room_id, room_receptacles, room_objects)
        rooms.append(room)

    scene = Scene(config, rooms, episode_data["instruction"])
    fig, ax = scene.plot(propositions, constraints)
    width_inches = 70
    fig.set_size_inches(
        width_inches, (scene.height / scene.width) * width_inches
    )
    if save_path:
        plt.savefig(save_path, dpi=300)
    else:
        plt.show()
    fig.clear()
    plt.close()
    scene.cleanup()
    del scene


def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Plot scene")
    parser.add_argument("--run-json", type=str, help="Path to run JSON file")
    parser.add_argument(
        "--episode-data-dir",
        type=str,
        help="Directory containing the episode metadata JSON files",
    )
    parser.add_argument("--episode-id", type=int, help="Index of episode")
    parser.add_argument(
        "--object-id", type=str, help="ID of a specific object to plot"
    )
    parser.add_argument(
        "--receptacle-id", type=str, help="ID of a specific receptacle to plot"
    )
    parser.add_argument(
        "--room-id", type=str, help="ID of a specific room to plot"
    )
    parser.add_argument(
        "--save-path", type=str, help="Directory to save the figures"
    )
    return parser.parse_args()


def main():
    """
    Main function to plot scenes based on provided arguments.
    """
    args = parse_arguments()
    config = load_configuration()

    current_dir = os.path.dirname(__file__)
    font_dirs = [os.path.join(current_dir, "fonts")]
    font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
    for font_file in font_files:
        font_manager.fontManager.addfont(font_file)

    plt.rcParams["font.family"] = "Inter"
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["text.color"] = "white"

    if args.episode_id is not None:
        episode_ids = [args.episode_id]
    else:
        episode_ids = sorted(
            [
                int(filename.split("_")[1].split(".")[0])
                for filename in os.listdir(args.episode_data_dir)
                if filename.startswith("episode_")
            ]
        )

    for episode_id in tqdm(episode_ids):
        try:
            episode_data = load_episode_data(args.episode_data_dir, episode_id)
            handle_to_recep = {
                v: k for k, v in episode_data["recep_to_handle"].items()
            }
            handle_to_object = {
                v: k for k, v in episode_data["object_to_handle"].items()
            }
            id_to_room = {v: k for k, v in episode_data["room_to_id"].items()}
            for receptacle_id in episode_data["recep_to_description"]:
                if not os.path.exists(
                    f'receptacles/{"_".join(receptacle_id.split("_")[:-1])}@2x.png'
                ):
                    print(
                        f"Missing receptacle asset for receptacle ID: {receptacle_id}"
                    )

            receptacle_icon_mapping = {
                receptacle_id: f'receptacles/{receptacle_id.split("_")[0]}@2x.png'
                for receptacle_id in episode_data["recep_to_description"]
                if os.path.exists(
                    f'receptacles/{receptacle_id.split("_")[0]}@2x.png'
                )
            }

            run_data = load_run_data(args.run_json, episode_id)

            # Handle Propositions
            propositions = run_data["evaluation_propositions"]
            for proposition in propositions:
                proposition["args"]["object_names"] = []
                for object_handle in proposition["args"]["object_handles"]:
                    proposition["args"]["object_names"].append(
                        handle_to_object[object_handle]
                    )
                if "receptacle_handles" in proposition["args"]:
                    proposition["args"]["receptacle_names"] = []
                    for recep_handle in proposition["args"][
                        "receptacle_handles"
                    ]:
                        proposition["args"]["receptacle_names"].append(
                            handle_to_recep[recep_handle]
                        )

                if "room_ids" in proposition["args"]:
                    proposition["args"]["room_names"] = []
                    for room_id in proposition["args"]["room_ids"]:
                        proposition["args"]["room_names"].append(
                            id_to_room[room_id]
                        )

            # Handle Constraints
            constraints = run_data["evaluation_constraints"]
            for idx, constraint in enumerate(constraints):
                if constraint["type"] == "TemporalConstraint":
                    digraph = nx.DiGraph(constraint["args"]["dag_edges"])
                    constraint["toposort"] = [
                        sorted(generation)
                        for generation in nx.topological_generations(digraph)
                    ]
                elif constraint["type"] == "TerminalSatisfactionConstraint":
                    unique_terminal_constraints = len(
                        np.unique(constraint["args"]["proposition_indices"])
                    )
                    assert len(propositions) == unique_terminal_constraints
                else:
                    print(
                        f"Constraint type {constraint['type']} is not handled currently. Deleting this constraint for the current visualization."
                    )
                    del constraints[idx]

            save_directory = (
                args.save_path
                if args.save_path
                else f"visualization_{episode_id}"
            )
            os.makedirs(save_directory, exist_ok=True)

            if args.object_id:
                plot_object(
                    config,
                    args.object_id,
                    os.path.join(save_directory, f"viz_{episode_id}.png"),
                )
            elif args.receptacle_id:
                plot_receptacle(
                    config,
                    args.receptacle_id,
                    receptacle_icon_mapping[args.receptacle_id],
                    os.path.join(save_directory, f"viz_{episode_id}.png"),
                )
            elif args.room_id:
                plot_room(
                    config,
                    args.room_id,
                    episode_data,
                    receptacle_icon_mapping,
                    os.path.join(save_directory, f"viz_{episode_id}.png"),
                )
            else:
                plot_scene(
                    config,
                    episode_data,
                    propositions,
                    constraints,
                    receptacle_icon_mapping,
                    os.path.join(save_directory, f"viz_{episode_id}.png"),
                )

        except Exception:
            print(f"Episode ID: {episode_id}")
            print(traceback.format_exc())


if __name__ == "__main__":
    main()
