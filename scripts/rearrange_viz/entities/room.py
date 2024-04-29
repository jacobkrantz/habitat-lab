import matplotlib.pyplot as plt
import os
import textwrap
from .placeholder import Placeholder

class Room:
    """
    Represents a room in a 2D space and provides methods for plotting it.
    """

    def __init__(self, config, room_id, receptacles, objects=None, use_full_height=False):
        """
        Initializes a Room instance.

        Parameters:
            config (object): A configuration object containing parameters for room rendering.
            room_id (str): Identifier for the room.
            receptacles (list): List of receptacles in the room.
            objects (list, optional): List of objects in the room. Defaults to None.
            use_full_height (bool, optional): Indicates if the room should use full_height. Defaults to False.
        """
        self.config = config.room
        self.room_id = room_id
        self.receptacles = receptacles
        self.objects = objects
        self.plot_placeholder = False

        if self.objects:
            self.use_full_height = True
        else:
            self.use_full_height = use_full_height

        self.init_size()
        
    def init_size(self):
        """
        Initializes the size of the room based on its receptacles and objects.
        """
        total_receptacle_width = max(self.config.min_width, sum(receptacle.width for receptacle in self.receptacles))
        self.room_width = total_receptacle_width + self.config.left_pad + self.config.right_pad
        self.width = self.room_width + 2 * self.config.horizontal_margin
 
        self.room_height = (self.config.full_height if self.use_full_height else self.config.half_height) + self.config.bottom_pad + self.config.top_pad
        self.height = self.room_height + 2 * self.config.vertical_margin
        
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
        """
        Plots the room on a matplotlib Axes.

        Parameters:
            position (tuple, optional): Position of the room's bottom-left corner. Defaults to (0, 0).
            ax (matplotlib.axes.Axes, optional): Axes to plot the room on.
                                                 If None, a new figure and Axes will be created.
                                                 Defaults to None.

        Returns:
            matplotlib.figure.Figure, matplotlib.axes.Axes or matplotlib.axes.Axes: If ax is None,
            returns the created figure and axes. Otherwise, returns the modified axes.
        """
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            created_fig = False

        new_position = [position[0] + self.config.horizontal_margin, position[1] + self.config.vertical_margin]

        # Calculate initial offset considering left margin and horizontal padding
        offset = new_position[0] + self.config.left_pad
        for receptacle in self.receptacles:
            ax = receptacle.plot(ax, position=(offset, new_position[1] + self.config.bottom_pad))
            offset += receptacle.width
        
        # Calculate total room width including margins
        total_receptacle_width = max(
            self.config.min_width, 
            sum(receptacle.width for receptacle in self.receptacles)
        )
        # Need to calculate room width AFTER plotting
        self.room_width = total_receptacle_width + self.config.left_pad + self.config.right_pad
        self.width = self.room_width + 2 * self.config.horizontal_margin 
        
        # Calculate text annotation position
        text_x = new_position[0] + self.room_width / 2
        text_y = new_position[1] + self.config.bottom_pad / 4   # Offset for lower v_pad region
        
        # Wrap the text if it's longer than a certain length
        wrapped_text = textwrap.fill(self.room_id, width=15)

        ax.annotate(wrapped_text, xy=(text_x, text_y), xytext=(text_x, text_y),
                    ha='center', va='bottom', fontsize=self.config.text_size)

        self.room_height = self.config.full_height + self.config.bottom_pad + self.config.top_pad   
        if self.objects:
            # Calculate initial offset for objects considering left margin, horizontal padding, and spacing objects evenly
            total_object_width = sum(obj.width for obj in self.objects)
            spacing = (self.room_width - total_object_width - self.config.object_block_horizontal_margin * 2) / (len(self.objects) + 1)
            offset = new_position[0] + spacing + self.config.object_block_horizontal_margin
            for obj in self.objects:
                ax = obj.plot(ax, position=(offset, new_position[1] + self.config.objects_height))  # Offset for objects above receptacles
                offset += obj.width + spacing  # Increment offset for next object and spacing
            
        else:
            if not self.use_full_height:
                self.room_height = self.config.half_height + self.config.bottom_pad + self.config.top_pad
            self.height = self.room_height + 2 * self.config.vertical_margin
        
        self.center_position = (new_position[0] + self.room_width / 2, new_position[1] + self.room_height / 2) 

        rect = ax.add_patch(plt.Rectangle((new_position[0], new_position[1]), self.room_width , self.room_height , color='#5A6F8E', alpha=self.config.box_alpha))
        # Set the z-order of the rectangle
        rect.set_zorder(-1)
        
        if self.plot_placeholder:
            self.center_placeholder = Placeholder(self.config)
            center_placeholder_origin = (self.center_position[0] - self.config.placeholder.width/2, self.center_position[1] - self.config.placeholder.height/2 )
            ax = self.center_placeholder.plot(ax, center_placeholder_origin)

        ax.set_xlim(position[0], position[0] + self.width)
        ax.set_ylim(position[1], position[1] + self.height)
        ax.axis('off')

        if created_fig:
            return fig, ax
        else:
            return ax
