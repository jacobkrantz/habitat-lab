import os
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.patches import FancyBboxPatch
import textwrap

from .constants import object_category_map, category_color_map

class Object:
    def __init__(self, config, object_id, icon_path=None):
        self.object_id = object_id
        self.icon_path = icon_path
        self.config = config.object
        self.center_position = None
    
    @property
    def width(self):
        return self.config.width
    
    @property
    def height(self):
        return self.config.height

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
            object_rect = FancyBboxPatch(
                (position[0], position[1]), 
                self.config.width, 
                self.config.height, 
                edgecolor='white', 
                facecolor=category_color_map[object_category_map['_'.join(self.object_id.split('_')[:-1])]], 
                linewidth=0, 
                linestyle='-', 
                boxstyle=f'Round, pad=0, rounding_size={self.config.rounding_size}', 
                alpha=1.0, 
            )

            ax.add_patch(object_rect)

        self.center_position = (position[0] + self.config.width / 2, position[1] + self.config.height / 2)
        text_position = (self.center_position[0], self.center_position[1] + self.config.text_margin)
        ax.annotate(self.object_id, 
                    xy=text_position,
                    ha='center', va='top', fontsize=self.config.text_size)
        
        if created_fig:
            return fig, ax
        else:
            return ax