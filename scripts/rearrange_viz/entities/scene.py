import os
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np

class Scene:
    def __init__(self, rooms, instruction=""):
        self.rooms = self.sort_rooms(rooms, instruction)
        
    def sort_rooms(self, rooms, instruction):
        if not instruction:
            return rooms

        # Split instruction string into words and exclude "room"
        keywords = [word.lower().strip(".") for word in instruction.split()]
        print(keywords)

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
                                line = mlines.Line2D([object_obj.center_position[0], receptacle_obj.center_placeholder_position[0]], 
                                                    [object_obj.center_position[1], receptacle_obj.center_placeholder_position[1]], 
                                                    linestyle=line_style, color='white', linewidth=float(os.environ['line_width']))
                                ax.add_line(line)
                                # Add arrow at the end of the line
                                self.add_arrow(line, (receptacle_obj.center_placeholder_position[0], receptacle_obj.center_placeholder_position[1]))
                            elif function_name == 'is_on_top':
                                if len(object_names) > 1:
                                    line_style = '--'  # Dotted line for multiple objects
                                else:
                                    line_style = '-'  # Solid line for single object
                                line = mlines.Line2D([object_obj.center_position[0], receptacle_obj.top_placeholder_position[0]], 
                                                    [object_obj.center_position[1], receptacle_obj.top_placeholder_position[1]], 
                                                    linestyle=line_style, color='white', linewidth=float(os.environ['line_width']))
                                ax.add_line(line)
                                # Add arrow at the end of the line
                                self.add_arrow(line, (receptacle_obj.top_placeholder_position[0], receptacle_obj.top_placeholder_position[1]))

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
                line = mlines.Line2D([object_obj.center_position[0], room_obj.center_position[0]], 
                                    [object_obj.center_position[1], room_obj.center_position[1]], 
                                    linestyle=line_style, color='white', linewidth=float(os.environ['line_width']))
                ax.add_line(line)
                # Add arrow at the end of the line
                self.add_arrow(line, (room_obj.center_position[0], room_obj.center_position[1]))

    def add_arrow(self, line, pos):
        """Add an arrow to the given line."""
        xdata = line.get_xdata()
        ydata = line.get_ydata()
        dx = xdata[1] - xdata[0]
        dy = ydata[1] - ydata[0]
        # Normalize the arrow length to 0.1
        scale = 0.1 / np.sqrt(dx**2 + dy**2)
        dx *= scale
        dy *= scale
        line.axes.annotate('', xy=(pos[0] + 100*dx, pos[1] + 100*dy), xytext=(pos[0] - dx, pos[1] - dy),
                            arrowprops=dict(facecolor='white', edgecolor='white', arrowstyle="->", linewidth=float(os.environ['line_width']), mutation_scale=4))

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
            for item in mentioned_items:
                found_receptacle = room.find_receptacle_by_id(item)
                found_object = room.find_object_by_id(item)
                if found_receptacle or found_object:
                    if room.room_id not in mentioned_rooms:
                        mentioned_rooms += [room.room_id]
                        room.margin = room.margin * 2
                if found_receptacle:
                    if '@2x' not in found_receptacle.icon_path:
                        found_receptacle.icon_path = found_receptacle.icon_path.replace('.png', '@2x.png')
                        found_receptacle.plot_placeholder = True
                        found_receptacle.init_size()
                        room.init_size()
        
        first_row_width = 0
        second_row_width = 0
        for room in self.rooms:
            if room.room_id in mentioned_rooms:
                for receptacle in room.receptacles:
                    if '@2x' not in receptacle.icon_path:
                        receptacle.icon_path = receptacle.icon_path.replace('.png', '@2x.png')
                        receptacle.init_size()
                        room.init_size()
            else:
                room.h_pad = 90
                room.v_pad = 150
                room.init_size()

        # Calculate total scene width based on the widths of all rooms
        first_row_width = sum(room.width for room in self.rooms if room.room_id in mentioned_rooms)
        second_row_width = sum(room.width for room in self.rooms if room.room_id not in mentioned_rooms)
        self.width = max(first_row_width, second_row_width)

        # Calculate scene height
        self.height = max(room.height for room in self.rooms)

        # Calculate starting position of the first row to center it relative to the second row
        first_row_position = (self.width - first_row_width) / 2
        second_row_position = 0

        # Create a figure and axis for plotting the scene
        fig, ax = plt.subplots()
        
        background_color = "#3E4C60"
        # Set the background color of the figure
        fig.patch.set_facecolor(background_color)

        # Plot rooms linearly with names underneath
        for room in self.rooms:
            if room.room_id in mentioned_rooms:
                ax = room.plot(position=(first_row_position, 0), ax=ax)
                first_row_position += room.width
            else:
                ax = room.plot(position=(second_row_position, -self.height), ax=ax)
                second_row_position += room.width

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
        ax.set_ylim(-self.height, self.height)
        return fig, ax
