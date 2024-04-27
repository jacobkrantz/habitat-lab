import os
import matplotlib.pyplot as plt
from PIL import Image
import textwrap
from .constants import receptacle_properties, receptacle_color_map
from .placeholder import Placeholder
from .utils import add_tint_to_rgb

class Receptacle:
    def __init__(self, config, receptacle_id, icon_path):
        self.config = config.receptacle
        self.receptacle_id = receptacle_id
        self.icon_path = icon_path
        self.center_placeholder_position = None  # Initialize center position
        self.top_placeholder_position = None  # Initialize top position
        self.plot_placeholder = False
        self.init_size()

    @property
    def horizontal_margin(self):
        return self.config.horizontal_margin

    def resize_icon(self, icon):
        width, height = icon.size
        scaling_factor = self.config.target_height / height

        # Resize the image
        new_width = int(width * scaling_factor)
        new_height = int(height * scaling_factor)
        resized_icon = icon.resize((new_width, new_height))
        return resized_icon

    def init_size(self):
        icon = Image.open(self.icon_path)
        icon = self.resize_icon(icon)
        icon_width, icon_height = icon.size
        self.width = (icon_width + 2 * self.horizontal_margin)
        self.height = icon_height

    def plot(self, ax=None, position=(0, 0)):
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            created_fig = False

        icon = Image.open(self.icon_path)
        icon = self.resize_icon(icon)
        color = receptacle_color_map['_'.join(self.receptacle_id.split('_')[:-1])]
        color = tuple(int(255 * i) for i in color)
        icon = add_tint_to_rgb(icon, tint_color=color)
        receptacle_width, receptacle_height = icon.size
        ax.imshow(icon, 
            extent=(
                (position[0] + self.horizontal_margin),
                (position[0] + receptacle_width + self.horizontal_margin), 
                position[1], 
                (position[1] + receptacle_height)
            )
        )

        self.center_placeholder_position = None
        self.top_placeholder_position = None
        if self.plot_placeholder:
            properties = receptacle_properties['_'.join(self.receptacle_id.split('_')[:-1])]
            if properties["is_on_top"]:
                self.top_placeholder_position = (position[0] + self.width / 2 + self.horizontal_margin, position[1] + self.height + self.config.placeholder_margin)  # Update top position
                self.top_placeholder = Placeholder(self.config)
                top_placeholder_origin = (self.top_placeholder_position[0] - self.config.placeholder.width/2, self.top_placeholder_position[1] - self.config.placeholder.height/2 )
                ax = self.top_placeholder.plot(ax, top_placeholder_origin)
                
            if properties["is_inside"]:
                self.center_placeholder_position = (position[0] + self.width / 2  + self.horizontal_margin, position[1] + self.height / 2)  # Update center position
                self.center_placeholder = Placeholder(self.config)
                center_placeholder_origin = (self.center_placeholder_position[0] - self.config.placeholder.width/2, self.center_placeholder_position[1] - self.config.placeholder.height/2 )
                ax = self.center_placeholder.plot(ax, center_placeholder_origin)

        # # Wrap the text if it's longer than a certain length
        # wrapped_text = textwrap.fill(self.receptacle_id, width=10)

        # ax.annotate(wrapped_text, 
        #             xy=((position[0] + self.width / 2), position[1] - 20),  # Use center position for annotation
        #             ha='center', va='top', color='black', fontsize=int(os.environ['receptacle_text_size']), rotation=20)
        
        ax.axis('off')

        if created_fig:
            return fig, ax
        else:
            return ax