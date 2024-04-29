import json
import os
import matplotlib.pyplot as plt
import argparse
from entities import Scene, Room, Receptacle, Object
from omegaconf import OmegaConf

import matplotlib.font_manager as font_manager


def main():
    """
    Main function to plot scenes based on provided arguments.
    """
    parser = argparse.ArgumentParser(description='Plot scene')
    parser.add_argument('--run-json', type=str, help='Path to run JSON file')
    parser.add_argument('--episode-data-dir', type=str, help='Directory containing the episode metadata JSON files')
    parser.add_argument('--episode-id', type=int, help='Index of episode')
    parser.add_argument('--object-id', type=str, help='ID of a specific object to plot')
    parser.add_argument('--receptacle-id', type=str, help='ID of a specific receptacle to plot')
    parser.add_argument('--room-id', type=str, help='ID of a specific room to plot')
    parser.add_argument('--save-path', type=str, help='Path to save the figure')
    args = parser.parse_args()

    # Get the directory of the current file
    current_dir = os.path.dirname(__file__)

    # Define the relative font directory
    font_dirs = [os.path.join(current_dir, 'fonts')]
    font_files = font_manager.findSystemFonts(fontpaths=font_dirs)
    for font_file in font_files:
        font_manager.fontManager.addfont(font_file)

    # # Print the list of available fonts
    # font_list = font_manager.fontManager.ttflist
    # for font in font_list:
    #     print(font)

    plt.rcParams["font.family"] = 'Inter'
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams['text.color'] = "white"

    run_json = args.run_json
    
    # Load the configuration
    config = OmegaConf.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), "conf/config.yaml"))

    with open(run_json) as f:
        run_data = json.load(f)
    with open(f"{args.episode_data_dir}/episode_{args.episode_id}.json") as f:
        episode_data = json.load(f)

    handle_to_recep = {v:k for k, v in episode_data["recep_to_handle"].items()}
    handle_to_object = {v:k for k, v in episode_data["object_to_handle"].items()}
    receptacle_icon_mapping = {
        receptacle_id: f'receptacles/{receptacle_id.split("_")[0]}@2x.png'
        for receptacle_id in list(episode_data['recep_to_description'].keys())
        if os.path.exists(f'receptacles/{receptacle_id.split("_")[0]}@2x.png')
    }

    
    for episode in run_data["episodes"]:
        if episode["episode_id"].split('|')[-1] == str(args.episode_id):
            propositions = episode["evaluation_propositions"]
            break
    
    for proposition in propositions:
        proposition["args"]["object_names"] = []
        for object_handle in proposition["args"]["object_handles"]:
            proposition["args"]["object_names"].append(handle_to_object[object_handle])
        
        proposition["args"]["receptacle_names"] = []
        for recep_handle in proposition["args"]["receptacle_handles"]:
            proposition["args"]["receptacle_names"].append(handle_to_recep[recep_handle])
        # TODO: Handle for `is_in_room` later

    if args.object_id:
        # Plot specific object
        object_id = args.object_id
        object = Object(config, object_id)
        fig, ax = object.plot()
        if args.save_path:
            plt.savefig(args.save_path, dpi=400)
        else:
            plt.show()
    elif args.receptacle_id:
        # Plot specific receptacle
        receptacle_id = args.receptacle_id
        receptacle = Receptacle(config, receptacle_id, receptacle_icon_mapping[receptacle_id])
        fig, ax = receptacle.plot()
        if args.save_path:
            plt.savefig(args.save_path, dpi=400)
        else:
            plt.show()
    elif args.room_id:
        # Plot specific room
        room_id = args.room_id
        objects = []
        for object_id in episode_data['object_to_room']:
            objects.append(Object(config, object_id))
            
        room_receptacles = []
        for receptacle_id, r_room_id in episode_data['recep_to_room'].items():
            if r_room_id == room_id:
                if receptacle_id in receptacle_icon_mapping:
                    room_receptacles.append(Receptacle(config, receptacle_id, receptacle_icon_mapping[receptacle_id]))
                else:
                    room_receptacles.append(Receptacle(config, receptacle_id, 'receptacles/chair@2x.png'))
        room_objects = [obj for obj in objects if episode_data['object_to_room'][obj.object_id] == room_id]
        room = Room(config, room_id, room_receptacles, room_objects)
        fig, ax = room.plot()
        if args.save_path:
            plt.savefig(args.save_path, dpi=400)
        else:
            plt.show()
    else:
        # Plot entire scene
        objects = []
        for object_id in episode_data['object_to_room']:
            objects.append(Object(config, object_id))
        rooms = []
        for room_id in episode_data['rooms']:
            room_receptacles = []
            for receptacle_id, r_room_id in episode_data['recep_to_room'].items():
                if r_room_id == room_id:
                    if receptacle_id in receptacle_icon_mapping:
                        room_receptacles.append(Receptacle(config, receptacle_id, receptacle_icon_mapping[receptacle_id]))
                    else:
                        room_receptacles.append(Receptacle(config, receptacle_id, 'receptacles/chair@2x.png'))
            room_objects = [obj for obj in objects if episode_data['object_to_room'][obj.object_id] == room_id]
            room = Room(config, room_id, room_receptacles, room_objects)
            rooms.append(room)

        # Plot the scene
        scene = Scene(config, rooms, episode_data["instruction"])
        fig, ax = scene.plot(propositions)
        width_inches = 70

        fig.set_size_inches(width_inches, (scene.height/scene.width) * width_inches)
        if args.save_path:
            plt.savefig(args.save_path, dpi=400)
        else:
            plt.show()

if __name__ == "__main__":
    main()
