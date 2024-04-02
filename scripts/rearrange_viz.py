import json
import os
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.patches import FancyBboxPatch
import matplotlib.lines as mlines
import textwrap

class Object:
    def __init__(self, object_id, icon_path=None):
        self.object_id = object_id
        self.icon_path = icon_path
        self.position_offset = 1
        self.bottom_center_position = None  # Initialize center position

        self.init_size()

    def init_size(self):
        self.width = 20
        self.height = 20

    def plot(self, ax=None, position=(0, 0)):
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            created_fig = False

        if self.icon_path is not None and os.path.exists(self.icon_path):
            icon = Image.open(self.icon_path)
            object_width, object_height = icon.size
            ax.imshow(icon, 
                extent=(
                    position[0],
                    position[0] + object_width,
                    position[1],
                    position[1] + object_height
                )
            )
        else:
            object_rect = FancyBboxPatch((position[0] + self.position_offset, position[1] + self.position_offset), self.width, self.height, edgecolor='black', facecolor='blue', linewidth=1, linestyle='-', boxstyle='Round, pad=0.05', alpha=0.7, antialiased=True)
            ax.add_patch(object_rect)

        self.bottom_center_position = (position[0] + self.width / 2 + self.position_offset, position[1]-10)  # Update center position

        # Wrap the text if it's longer than a certain length
        wrapped_text = textwrap.fill(self.object_id, width=10)

        ax.annotate(wrapped_text, 
                    xy=(position[0] + self.width / 2 + self.position_offset, position[1] + self.position_offset),  # Use center position for annotation
                    ha='center', va='top', color='black', fontsize=object_text_size)
        
        if created_fig:
            return fig, ax
        else:
            return ax

class Receptacle:
    def __init__(self, receptacle_id, icon_path, scale=1.0):
        self.receptacle_id = receptacle_id
        self.icon_path = icon_path
        self.margin = 10
        self.scale = scale
        self.center_position = None  # Initialize center position
        self.top_position = None  # Initialize top position

        self.init_size()

    def init_size(self):
        icon = Image.open(self.icon_path)
        icon_width, icon_height = icon.size
        self.width = (icon_width + 2 * self.margin)
        self.height = (icon_height + 20)

    def plot(self, ax=None, position=(0, 0)):
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            created_fig = False

        icon = Image.open(self.icon_path)
        receptacle_width, receptacle_height = icon.size
        ax.imshow(icon, 
            extent=(
                (position[0] + self.margin),
                (position[0] + receptacle_width + self.margin), 
                position[1], 
                (position[1] + receptacle_height + 20)
            )
        )

        self.center_position = (position[0] + self.width / 2, position[1] + self.height / 2)  # Update center position
        self.top_position = (position[0] + self.width / 2, position[1] + self.height)  # Update top position

        # Wrap the text if it's longer than a certain length
        wrapped_text = textwrap.fill(self.receptacle_id, width=10)

        ax.annotate(wrapped_text, 
                    xy=((position[0] + self.width / 2), position[1]),  # Use center position for annotation
                    ha='center', va='top', color='black', fontsize=receptacle_text_size)
        
        ax.axis('off')

        if created_fig:
            return fig, ax
        else:
            return ax

class Room:
    def __init__(self, room_id, receptacles, objects=None, scale=1.0):
        self.room_id = room_id
        self.receptacles = receptacles
        self.objects = objects

        self.alpha = 0.5
        self.margin = 10
        self.scale = scale
        self.room_height = 600
        
        self.min_width = 400
        self.object_height = 500
        self.width = None
        self.height = None
        self.init_size()
        
    def init_size(self):
        total_receptacle_width = max(self.min_width, sum(receptacle.width for receptacle in self.receptacles))
        room_width = total_receptacle_width
        self.width = (room_width + 2 * self.margin) 
        self.height = self.room_height
        
    def find_object_by_id(self, object_id):
        """
        Find an object by its ID.

        Args:
            object_id (str): The ID of the object to find.

        Returns:
            Object or None: The object if found, otherwise None.
        """
        if self.objects:
            for obj in self.objects:
                if obj.object_id == object_id:
                    return obj
        return None

    def find_receptacle_by_id(self, receptacle_id):
        """
        Find a receptacle by its ID.

        Args:
            receptacle_id (str): The ID of the receptacle to find.

        Returns:
            Receptacle or None: The receptacle if found, otherwise None.
        """
        for receptacle in self.receptacles:
            if receptacle.receptacle_id == receptacle_id:
                return receptacle
        return None

    def plot(self, position=(0, 0), ax=None):
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            created_fig = False

        # Calculate total room width including margins
        total_receptacle_width = max(self.min_width, sum(receptacle.width for receptacle in self.receptacles))
        room_width = total_receptacle_width

        ax.add_patch(plt.Rectangle((position[0] + self.margin, position[1]), room_width , self.room_height , color='lightgray', alpha=self.alpha))
        
        ax.annotate(self.room_id, xy=(position[0] + self.margin + room_width  / 2, position[1]), xytext=(position[0] + room_width  / 2, position[1] - 20 ),
                    ha='center', va='top', color='black', fontsize=room_text_size)

        # Calculate initial offset considering left margin
        offset = position[0] + self.margin
        for receptacle in self.receptacles:
            ax = receptacle.plot(ax, position=(offset, position[1]))
            offset += receptacle.width

        if self.objects:
            # Calculate initial offset for objects considering left margin and spacing objects evenly
            total_object_width = sum(obj.width for obj in self.objects)
            spacing = (room_width - total_object_width) / (len(self.objects) + 1)
            offset = position[0] + self.margin + spacing
            for obj in self.objects:
                ax = obj.plot(ax, position=(offset, position[1] + self.object_height))  # Offset for objects above receptacles
                offset += obj.width + spacing  # Increment offset for next object and spacing


        ax.set_xlim(position[0], position[0] + (2 * self.margin + room_width) )
        ax.set_ylim(position[1], position[1] + self.room_height )
        ax.axis('off')

        if created_fig:
            return fig, ax
        else:
            return ax

class Scene:
    def __init__(self, rooms):
        self.rooms = rooms

    def plot(self, propositions=None):
        # Calculate total scene width based on the widths of all rooms
        self.width = sum(room.width for room in self.rooms)
        self.height = max(room.height for room in self.rooms)

        # Create a figure and axis for plotting the scene
        fig, ax = plt.subplots()

        # Plot rooms linearly with names underneath
        x_position = 0
        for room in self.rooms:
            ax = room.plot(position=(x_position, 0), ax=ax)
            ax.annotate(room.room_id, xy=(x_position + room.width / 2, -20), ha='center', va='top', color='black')
            x_position += room.width

        # Plot lines between objects and receptacles based on propositions
        if propositions:
            for proposition in propositions:
                function_name = proposition['function_name']
                args = proposition['args']
                object_names = args['object_names']
                receptacle_names = args['receptacle_names']
                number = args['number']

                for object_name in object_names:
                    for room in self.rooms:
                        object_obj = room.find_object_by_id(object_name)
                        if object_obj:
                            for receptacle_name in receptacle_names:
                                receptacle_objs = []
                                for r_room in self.rooms:
                                    receptacle_obj = r_room.find_receptacle_by_id(receptacle_name)
                                    if receptacle_obj:
                                        receptacle_objs.append(receptacle_obj)

                                for receptacle_obj in receptacle_objs:
                                    if function_name == 'is_inside':
                                        if len(object_names) > 1:
                                            line_style = '--'  # Dotted line for multiple objects
                                        else:
                                            line_style = '-'  # Solid line for single object
                                        line = mlines.Line2D([object_obj.bottom_center_position[0], receptacle_obj.center_position[0]], 
                                                            [object_obj.bottom_center_position[1], receptacle_obj.center_position[1]], 
                                                            linestyle=line_style, color='black', linewidth=line_width)
                                        ax.add_line(line)
                                    elif function_name == 'is_on_top':
                                        if len(object_names) > 1:
                                            line_style = '--'  # Dotted line for multiple objects
                                        else:
                                            line_style = '-'  # Solid line for single object
                                        line = mlines.Line2D([object_obj.bottom_center_position[0], receptacle_obj.top_position[0]], 
                                                            [object_obj.bottom_center_position[1], receptacle_obj.top_position[1]], 
                                                            linestyle=line_style, color='black', linewidth=line_width)
                                        ax.add_line(line)

        # Set axis limits
        ax.set_xlim(0, self.width)
        ax.set_ylim(0, self.height)
        return fig, ax



if __name__ == "__main__":
    # scene_json_path = 'habitat_scene_metadata/metadata_ex_102344049.json'
    scene_json_path = 'habitat_scene_metadata/metadata_ex_102344049.json'
    with open(scene_json_path) as f:
        scene_data = json.load(f)

    receptacle_icon_mapping = {
        receptacle_id: f'receptacles/{receptacle_id.split("_")[0]}.png'
        for receptacle_id in scene_data['receptacles']
        if os.path.exists(f'receptacles/{receptacle_id.split("_")[0]}.png')
    }
    propositions_path = 'propositions/eval_propositions_ex_102344049.json'
    with open(propositions_path) as f:
        propositions = json.load(f)["propositions"]

    receptacle_text_size = 2
    room_text_size = 6
    object_text_size = 2
    line_width = 0.5
    
    
    # Object Plotting
    # object_id = "chair_0"
    # object = Object(object_id)
    # fig, ax = object.plot()
    # plt.show()

    # Receptacle Plotting
    # receptacle_id = "chair_0"
    # receptacle = Receptacle(receptacle_id, receptacle_icon_mapping[receptacle_id])
    # fig, ax = receptacle.plot()
    # plt.show()
    
    # Room Plotting
    # Create objects
    objects = []
    for object_id in scene_data['object_to_room']:
        # object_path = f'objects/{object_id.split("_")[0]}.png'
        objects.append(Object(object_id))
    room_id = "kitchen_0"
    room_receptacles = [Receptacle(receptacle_id, receptacle_icon_mapping[receptacle_id]) for receptacle_id, r_room_id in scene_data['recep_to_room'].items() if r_room_id == room_id]
    room_objects = [obj for obj in objects if scene_data['object_to_room'][obj.object_id] == room_id]
    print(len(room_objects))
    room = Room(room_id, room_receptacles, room_objects)
    fig, ax = room.plot()
    plt.show()
    
    # # Scene Plotting
    
    # objects = []
    # for object_id in scene_data['object_to_room']:
    #     # object_path = f'objects/{object_id.split("_")[0]}.png'
    #     objects.append(Object(object_id))
    # rooms = []
    # for room_id in scene_data['rooms']:
    #     room_receptacles = []
    #     for receptacle_id, r_room_id in scene_data['recep_to_room'].items():
    #         if r_room_id == room_id:
    #             if receptacle_id in receptacle_icon_mapping:
    #                 room_receptacles.append(Receptacle(receptacle_id, receptacle_icon_mapping[receptacle_id]))
    #             else:
    #                 print(receptacle_id)
    #                 room_receptacles.append(Receptacle(receptacle_id, 'receptacles/chair.png'))
    #     room_objects = [obj for obj in objects if scene_data['object_to_room'][obj.object_id] == room_id]
    #     room = Room(room_id, room_receptacles, room_objects)
    #     rooms.append(room)

    # # Plot the scene
    # scene = Scene(rooms)
    # fig, ax = scene.plot(propositions)
    # width_inches = 20
    # fig.set_size_inches(width_inches, (scene.height/scene.width) * width_inches)
    # plt.savefig('test.png', dpi=400)
    

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
