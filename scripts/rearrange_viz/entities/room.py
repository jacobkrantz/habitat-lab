import matplotlib.pyplot as plt
import os
import textwrap
from .placeholder import Placeholder

class Room:
    def __init__(self, config, room_id, receptacles, objects=None, in_proposition=False):
        self.config = config.room
        self.room_id = room_id
        self.receptacles = receptacles
        self.objects = objects
        self.plot_placeholder = False

        self.in_proposition = in_proposition
        if self.objects:
            self.room_height = self.config.full_height
        else:
            if in_proposition:
                self.room_height = self.config.full_height
            else:
                self.room_height = self.config.half_height

        self.init_size()
        
    def init_size(self):
        total_receptacle_width = max(self.config.min_width, sum(receptacle.width for receptacle in self.receptacles))
        room_width = total_receptacle_width
        self.width = (room_width + 2 * self.config.horizontal_margin + self.config.left_pad + self.config.right_pad) 
        total_room_height = self.room_height + self.config.bottom_pad + self.config.top_pad
        self.height = total_room_height + 2 * self.config.vertical_margin
        
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

        new_position = [position[0] + self.config.horizontal_margin, position[1] + self.config.vertical_margin]

        # Calculate initial offset considering left margin and horizontal padding
        offset = new_position[0] + self.config.left_pad
        for receptacle in self.receptacles:
            ax = receptacle.plot(ax, position=(offset, new_position[1] + self.config.bottom_pad))
            print(receptacle.width)
            offset += receptacle.width

        
        # Calculate total room width including margins
        total_receptacle_width = max(
            self.config.min_width, 
            sum(receptacle.width for receptacle in self.receptacles)
        )
        # Need to calculate room width AFTER plotting
        room_width = total_receptacle_width + self.config.left_pad + self.config.right_pad
        self.width = room_width + 2 * self.config.horizontal_margin 
        
        # Calculate text annotation position
        text_x = new_position[0] + room_width / 2
        text_y = new_position[1] + self.config.bottom_pad / 4   # Offset for lower v_pad region
        
        # Wrap the text if it's longer than a certain length
        wrapped_text = textwrap.fill(self.room_id, width=15)

        ax.annotate(wrapped_text, xy=(text_x, text_y), xytext=(text_x, text_y),
                    ha='center', va='bottom', fontsize=self.config.text_size)

        total_room_height = self.config.full_height + self.config.bottom_pad + self.config.top_pad   
        if self.objects:
            # Calculate initial offset for objects considering left margin, horizontal padding, and spacing objects evenly
            total_object_width = sum(obj.width for obj in self.objects)
            spacing = (room_width - total_object_width - self.config.object_block_horizontal_margin * 2) / (len(self.objects) + 1)
            offset = new_position[0] + spacing + self.config.object_block_horizontal_margin
            for obj in self.objects:
                ax = obj.plot(ax, position=(offset, new_position[1] + self.config.objects_height))  # Offset for objects above receptacles
                offset += obj.width + spacing  # Increment offset for next object and spacing
                
        else:
            if not self.in_proposition:
                total_room_height = self.config.half_height + self.config.bottom_pad + self.config.top_pad
            self.height = total_room_height + 2 * self.config.vertical_margin
        
        self.center_position = (new_position[0] + room_width / 2, new_position[1] + self.height / 2) 

        rect = ax.add_patch(plt.Rectangle((new_position[0], new_position[1]), room_width , total_room_height , color='#5A6F8E', alpha=self.config.box_alpha))
        # Set the z-order of the rectangle
        rect.set_zorder(-1)
        
        if self.plot_placeholder:
            self.center_placeholder = Placeholder(self.config)
            center_placeholder_origin = (self.center_position[0] - self.config.placeholder.width/2, self.center_position[1] - self.config.placeholder.height/2 )
            ax = self.center_placeholder.plot(ax, center_placeholder_origin)

        ax.set_xlim(position[0], position[0] + (2 * self.config.horizontal_margin + room_width))
        ax.set_ylim(position[1], position[1] + self.height)
        ax.axis('off')

        if created_fig:
            return fig, ax
        else:
            return ax