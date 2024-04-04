import os
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.patches import FancyBboxPatch
import textwrap

class Object:
    def __init__(self, object_id, icon_path=None):
        self.object_id = object_id
        self.icon_path = icon_path
        self.position_offset = 1
        self.bottom_center_position = None  # Initialize center position

        self.init_size()

    def init_size(self):
        self.width = 20
        self.height = 20

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
            object_rect = FancyBboxPatch((position[0] + self.position_offset, position[1] + self.position_offset), self.width, self.height, edgecolor='black', facecolor='blue', linewidth=1, linestyle='-', boxstyle='Round, pad=0.05', alpha=0.7, antialiased=True)
            ax.add_patch(object_rect)

        self.bottom_center_position = (position[0] + self.width / 2 + self.position_offset, position[1]-10)  # Update center position

        # Wrap the text if it's longer than a certain length
        wrapped_text = textwrap.fill(self.object_id, width=10)

        ax.annotate(wrapped_text, 
                    xy=(position[0] + self.width / 2 + self.position_offset, position[1] + self.position_offset),  # Use center position for annotation
                    ha='center', va='top', color='black', fontsize=int(os.environ['object_text_size']))
        
        if created_fig:
            return fig, ax
        else:
            return ax