import json
import os
import matplotlib.pyplot as plt
import matplotlib as mpl
import argparse
from entities import Scene, Room, Receptacle, Object

def main():
    parser = argparse.ArgumentParser(description='Plot scene')
    parser.add_argument('--scene-json-path', type=str, help='Path to scene JSON file')
    parser.add_argument('--propositions-path', type=str, help='Path to propositions JSON file')
    parser.add_argument('--receptacle-text-size', type=int, default=2, help='Text size for receptacle annotations')
    parser.add_argument('--room-text-size', type=int, default=3, help='Text size for room annotations')
    parser.add_argument('--object-text-size', type=int, default=2, help='Text size for object annotations')
    parser.add_argument('--line-width', type=float, default=0.4, help='Width of lines connecting objects and receptacles')
    parser.add_argument('--object-id', type=str, help='ID of a specific object to plot')
    parser.add_argument('--receptacle-id', type=str, help='ID of a specific receptacle to plot')
    parser.add_argument('--room-id', type=str, help='ID of a specific room to plot')
    parser.add_argument('--save-path', type=str, help='Path to save the figure')
    args = parser.parse_args()

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams['text.color'] = "white"

    scene_json_path = args.scene_json_path
    propositions_path = args.propositions_path
    os.environ['receptacle_text_size'] = str(args.receptacle_text_size)
    os.environ['room_text_size'] = str(args.room_text_size)
    os.environ['object_text_size'] = str(args.object_text_size)
    os.environ['line_width'] = str(args.line_width)

    with open(scene_json_path) as f:
        scene_data = json.load(f)

    receptacle_icon_mapping = {
        receptacle_id: f'receptacles/{receptacle_id.split("_")[0]}.png'
        for receptacle_id in scene_data['receptacles']
        if os.path.exists(f'receptacles/{receptacle_id.split("_")[0]}.png')
    }

    with open(propositions_path) as f:
        propositions = json.load(f)["propositions"]

    if args.object_id:
        # Plot specific object
        object_id = args.object_id
        object = Object(object_id)
        fig, ax = object.plot()
        if args.save_path:
            plt.savefig(args.save_path, dpi=400)
        else:
            plt.show()
    elif args.receptacle_id:
        # Plot specific receptacle
        receptacle_id = args.receptacle_id
        receptacle = Receptacle(receptacle_id, receptacle_icon_mapping[receptacle_id])
        fig, ax = receptacle.plot()
        if args.save_path:
            plt.savefig(args.save_path, dpi=400)
        else:
            plt.show()
    elif args.room_id:
        # Plot specific room
        room_id = args.room_id
        objects = []
        for object_id in scene_data['object_to_room']:
            objects.append(Object(object_id))
            
        room_receptacles = []
        for receptacle_id, r_room_id in scene_data['recep_to_room'].items():
            if r_room_id == room_id:
                if receptacle_id in receptacle_icon_mapping:
                    room_receptacles.append(Receptacle(receptacle_id, receptacle_icon_mapping[receptacle_id]))
                else:
                    room_receptacles.append(Receptacle(receptacle_id, 'receptacles/chair.png'))
        room_objects = [obj for obj in objects if scene_data['object_to_room'][obj.object_id] == room_id]
        room = Room(room_id, room_receptacles, room_objects)
        fig, ax = room.plot()
        if args.save_path:
            plt.savefig(args.save_path, dpi=400)
        else:
            plt.show()
    else:
        # Plot entire scene
        objects = []
        for object_id in scene_data['object_to_room']:
            objects.append(Object(object_id))
        rooms = []
        for room_id in scene_data['rooms']:
            room_receptacles = []
            for receptacle_id, r_room_id in scene_data['recep_to_room'].items():
                if r_room_id == room_id:
                    if receptacle_id in receptacle_icon_mapping:
                        room_receptacles.append(Receptacle(receptacle_id, receptacle_icon_mapping[receptacle_id]))
                    else:
                        print(receptacle_id)
                        room_receptacles.append(Receptacle(receptacle_id, 'receptacles/chair.png'))
            room_objects = [obj for obj in objects if scene_data['object_to_room'][obj.object_id] == room_id]
            room = Room(room_id, room_receptacles, room_objects)
            rooms.append(room)

        # Plot the scene
        scene = Scene(rooms, scene_data["instruction"])
        fig, ax = scene.plot(propositions)
        width_inches = 20
        fig.set_size_inches(width_inches, (scene.height/scene.width) * width_inches)
        if args.save_path:
            plt.savefig(args.save_path, dpi=400)
        else:
            plt.show()

if __name__ == "__main__":
    main()

# python scripts/rearrange_viz/viz.py --scene-json-path habitat_scene_metadata/metadata_ex_102344049.json --propositions-path propositions/eval_propositions_ex_102344049.json 


# TODOs:
# Sort in two stacks - used vs unused rooms.
# Use slanted text to reduce horizontal width.
# Squeeze receptacles and objects.
# Use arguments to specify
# Add is_in_room proposition logic
# Maybe use color for receptacles/objects?
    # Add color programmatically
# Room-receptacle inconsistency to be handled in the code
# Screen succession
# Next functionality: mechanical turk app? Either someone coaching or doing it.
