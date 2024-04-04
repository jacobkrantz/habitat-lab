import os
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

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
                                                            linestyle=line_style, color='black', linewidth=float(os.environ['line_width']))
                                        ax.add_line(line)
                                    elif function_name == 'is_on_top':
                                        if len(object_names) > 1:
                                            line_style = '--'  # Dotted line for multiple objects
                                        else:
                                            line_style = '-'  # Solid line for single object
                                        line = mlines.Line2D([object_obj.bottom_center_position[0], receptacle_obj.top_position[0]], 
                                                            [object_obj.bottom_center_position[1], receptacle_obj.top_position[1]], 
                                                            linestyle=line_style, color='black', linewidth=float(os.environ['line_width']))
                                        ax.add_line(line)

        # Set axis limits
        ax.set_xlim(0, self.width)
        ax.set_ylim(0, self.height)
        return fig, ax
