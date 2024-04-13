import matplotlib.pyplot as plt
import os
import textwrap

class Room:
    def __init__(self, room_id, receptacles, objects=None, scale=1.0):
        self.room_id = room_id
        self.receptacles = receptacles
        self.objects = objects

        self.alpha = 1
        self.margin = 10
        self.v_pad = 150
        self.h_pad = 200
        self.scale = scale
        self.room_height = 700
        
        self.min_width = 100
        self.object_height = 500
        self.width = None
        self.height = None
        self.object_block_offset = 300
        self.init_size()
        
    def init_size(self):
        total_receptacle_width = max(self.min_width, sum(receptacle.width for receptacle in self.receptacles))
        room_width = total_receptacle_width
        self.width = (room_width + 2 * self.margin + 2 * self.h_pad) 
        self.height = self.room_height + 2 * self.v_pad
        
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
        room_width = total_receptacle_width + 2 * self.h_pad

        self.center_position = (position[0] + self.margin + room_width / 2, position[1] + self.room_height / 2) 

        # Calculate text annotation position
        text_x = position[0] + self.margin + room_width / 2
        text_y = position[1] + self.v_pad / 4   # Offset for lower v_pad region
        
        # Wrap the text if it's longer than a certain length
        wrapped_text = textwrap.fill(self.room_id, width=15)

        ax.annotate(wrapped_text, xy=(text_x, text_y), xytext=(text_x, text_y),
                    ha='center', va='bottom', fontsize=int(os.environ['room_text_size']))

        # Calculate initial offset considering left margin and horizontal padding
        offset = position[0] + self.margin + self.h_pad
        for receptacle in self.receptacles:
            ax = receptacle.plot(ax, position=(offset, position[1] + self.v_pad))
            offset += receptacle.width

        if self.objects:
            # Calculate initial offset for objects considering left margin, horizontal padding, and spacing objects evenly
            total_object_width = sum(obj.width for obj in self.objects)
            spacing = (room_width - total_object_width - self.object_block_offset * 2) / (len(self.objects) + 1)
            offset = position[0] + self.margin + spacing + self.object_block_offset
            for obj in self.objects:
                ax = obj.plot(ax, position=(offset, position[1] + self.object_height))  # Offset for objects above receptacles
                offset += obj.width + spacing  # Increment offset for next object and spacing
        
        rect = ax.add_patch(plt.Rectangle((position[0] + self.margin, position[1]), room_width , self.room_height , color='#5A6F8E', alpha=self.alpha))
        # Set the z-order of the rectangle
        rect.set_zorder(-1)

        ax.set_xlim(position[0], position[0] + (2 * self.margin + room_width))
        ax.set_ylim(position[1], position[1] + self.room_height + 2 * self.v_pad)
        ax.axis('off')

        if created_fig:
            return fig, ax
        else:
            return ax