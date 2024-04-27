import os
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.patches import FancyArrow
import numpy as np

class Scene:
    def __init__(self, config, rooms, instruction=""):
        self.config = config.scene
        self.rooms = self.sort_rooms(rooms, instruction)
        
    def sort_rooms(self, rooms, instruction):
        if not instruction:
            return rooms

        # Split instruction string into words and exclude "room"
        keywords = [word.lower().strip(".") for word in instruction.split()]

        # Create a dictionary to hold the rooms and their relevance score
        relevance_scores = {}

        for room in rooms:
            score = sum(" ".join(room.room_id.split("_")[:-1]) in keyword for keyword in keywords)

            # Consider receptacles in the score calculation
            for receptacle in room.receptacles:
                score += sum(" ".join(receptacle.receptacle_id.split("_")[:-1]) in keyword for keyword in keywords)

            # Consider objects in the score calculation
            if room.objects:
                for obj in room.objects:
                    score += sum(" ".join(obj.object_id.split("_")[:-1]) in keyword for keyword in keywords)

            relevance_scores[room] = score

        # Sort the rooms based on relevance score
        sorted_rooms = sorted(relevance_scores.keys(), key=lambda room: relevance_scores[room], reverse=True)

        return sorted_rooms
        
    def plot_object_to_receptacle_lines(self, object_names, receptacle_names, function_name, ax):
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
                                # line = mlines.Line2D([object_obj.center_position[0], receptacle_obj.center_placeholder_position[0]], 
                                #                     [object_obj.center_position[1], receptacle_obj.center_placeholder_position[1]], 
                                #                     linestyle=line_style, color='white', linewidth=self.config.linewidth)
                                # ax.add_line(line)
                                # Add arrow at the end of the line
                                self.add_arrow(ax, object_obj.center_position, receptacle_obj.center_placeholder_position, line_style)
                            elif function_name == 'is_on_top':
                                if len(object_names) > 1:
                                    line_style = '--'  # Dotted line for multiple objects
                                else:
                                    line_style = '-'  # Solid line for single object
                                # Add arrow at the end of the line
                                self.add_arrow(ax, object_obj.center_position,  receptacle_obj.top_placeholder_position, line_style)

    def plot_object_to_room_lines(self, object_names, room_names, ax):
        source_objects = []
        target_rooms = []
        for object_name in object_names:
            for room in self.rooms:
                object_obj = room.find_object_by_id(object_name)
                if object_obj:
                    source_objects.append(object_obj)
        for room_name in room_names:
            for r_room in self.rooms:
                if r_room.room_id == room_name:
                    target_rooms.append(r_room)
        for object_obj in source_objects:        
            for room_obj in target_rooms:
                if len(object_names) > 1:
                    line_style = '--'  # Dotted line for multiple objects
                else:
                    line_style = '-'  # Solid line for single object

                self.add_arrow(ax, object_obj.center_position, room_obj.center_position, line_style)

    def add_arrow(self, ax, obj_loc, room_loc, line_style):
        """Add an arrow to the given line."""
        arrow = FancyArrow(obj_loc[0], obj_loc[1], room_loc[0] - obj_loc[0], room_loc[1] - obj_loc[1], linestyle=line_style,
                        head_length=self.config.arrow.head_length, head_width=self.config.arrow.head_width, width=self.config.arrow.linewidth, linewidth=self.config.arrow.linewidth,
                        length_includes_head=True, edgecolor='white', facecolor='white', overhang=self.config.arrow.overhang)
        ax.add_patch(arrow)

    def plot_rooms_linear(self, mentioned_rooms, ax):
        # Plot rooms linearly with names underneath
        # Calculate total scene width based on the widths of all rooms
        self.width = sum(room.width for room in self.rooms if room.room_id in mentioned_rooms)
        # Calculate scene height
        first_row_height = max(room.height for room in self.rooms if room.room_id in mentioned_rooms)

        # Calculate starting position of the first row to center it relative to the second row
        first_row_position = 0
        for room in self.rooms:
            if room.room_id in mentioned_rooms:
                ax = room.plot(position=(first_row_position, 0), ax=ax)
                first_row_position += room.width

        
        total_rooms = len(self.rooms)
        current_rooms_to_plot = []
        current_row_width = 0
        current_row_height = 0
        i = 0
        while i < total_rooms:
            room = self.rooms[i]    
            if room.room_id not in mentioned_rooms:
                if room.width + current_row_width <= self.width:
                    current_row_width += room.width
                    current_rooms_to_plot.append(room)
                else:
                    current_row_height -= max(room.height for room in current_rooms_to_plot)
                    current_row_width = 0
                    for room in current_rooms_to_plot:
                        ax = room.plot(position=(current_row_width, current_row_height), ax=ax)
                        current_row_width += room.width
                    current_row_width = 0
                    current_rooms_to_plot = []
                    continue
            i+=1

        current_row_height -= max(room.height for room in current_rooms_to_plot)
        current_row_width = 0
        for room in current_rooms_to_plot:
            ax = room.plot(position=(current_row_width, current_row_height), ax=ax)
            current_row_width += room.width
        

        self.height_upper = first_row_height
        self.height_lower = current_row_height
        self.height = self.height_upper - self.height_lower

        return ax

    def plot(self, propositions=None):
        # Extract room names mentioned in propositions
        mentioned_items = []
        mentioned_rooms = []
        if propositions:
            for prop in propositions:
                if prop["function_name"] != "is_in_room":
                    mentioned_items += prop['args']['object_names']
                    mentioned_items += prop['args']['receptacle_names']
                else:
                    mentioned_items += prop['args']['object_names']
                    mentioned_rooms += prop['args']['room_names']

        for room in self.rooms:
            if room.room_id in mentioned_rooms:
                room.plot_placeholder = True

        for room in self.rooms:
            for item in mentioned_items:
                found_receptacle = room.find_receptacle_by_id(item)
                found_object = room.find_object_by_id(item)
                if found_receptacle or found_object:
                    if room.room_id not in mentioned_rooms:
                        mentioned_rooms += [room.room_id]
                if found_receptacle:
                    found_receptacle.plot_placeholder = True

        for room in self.rooms:
            if room.room_id in mentioned_rooms:
                room.in_proposition=True
                room.init_size()

        # Create a figure and axis for plotting the scene
        fig, ax = plt.subplots()
        
        background_color = "#3E4C60"
        # Set the background color of the figure
        fig.patch.set_facecolor(background_color)

        ax = self.plot_rooms_linear(mentioned_rooms, ax)

        # Plot lines between objects and receptacles based on propositions
        if propositions:
            for proposition in propositions:
                function_name = proposition['function_name']
                args = proposition['args']
                object_names = args['object_names']
                if function_name != "is_in_room":
                    receptacle_names = args['receptacle_names']
                    self.plot_object_to_receptacle_lines(object_names, receptacle_names, function_name, ax)
                else:
                    room_names = args['room_names']
                    self.plot_object_to_room_lines(object_names, room_names, ax)

        # Set axis limits
        ax.set_xlim(0, self.width)
        ax.set_ylim(self.height_lower, self.height_upper)
        return fig, ax