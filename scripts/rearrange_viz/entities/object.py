import os
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.patches import FancyBboxPatch
import textwrap

from .constants import object_category_map, category_color_map

class Object:
    def __init__(self, object_id, icon_path=None):
        self.object_id = object_id
        self.icon_path = icon_path
        self.center_position = None  # Initialize center position
        self.text_offset = 60
        self.init_size()

    def init_size(self):
        self.width = 40
        self.height = 40

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
                self.width, 
                self.height, 
                edgecolor='white', 
                facecolor=category_color_map[object_category_map['_'.join(self.object_id.split('_')[:-1])]], 
                linewidth=0, 
                linestyle='-', 
                boxstyle='Round, pad=0, rounding_size=4', 
                alpha=1.0, 
            )

            ax.add_patch(object_rect)

        self.center_position = (position[0] + self.width / 2, position[1] + self.height / 2)  # Update center position

        # Wrap the text if it's longer than a certain length
        wrapped_text = textwrap.fill(self.object_id, width=12)

        ax.annotate(wrapped_text, 
                    xy=(position[0] + self.width / 2, position[1] + self.height + self.text_offset),  # Use center position for annotation
                    ha='center', va='top', fontsize=int(os.environ['object_text_size']))
        
        if created_fig:
            return fig, ax
        else:
            return ax
        
