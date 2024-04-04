import matplotlib.pyplot as plt
import os

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
                    ha='center', va='top', color='black', fontsize=int(os.environ['room_text_size']))

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