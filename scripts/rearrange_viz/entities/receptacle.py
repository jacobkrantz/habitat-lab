import os
import matplotlib.pyplot as plt
from PIL import Image
import textwrap

class Receptacle:
    def __init__(self, receptacle_id, icon_path, scale=1.0):
        self.receptacle_id = receptacle_id
        self.icon_path = icon_path
        self.margin = 10
        self.scale = scale
        self.center_position = None  # Initialize center position
        self.top_position = None  # Initialize top position

        self.init_size()

    def init_size(self):
        icon = Image.open(self.icon_path)
        icon_width, icon_height = icon.size
        self.width = (icon_width + 2 * self.margin)
        self.height = (icon_height + 20)

    def plot(self, ax=None, position=(0, 0)):
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            created_fig = False

        icon = Image.open(self.icon_path)
        receptacle_width, receptacle_height = icon.size
        ax.imshow(icon, 
            extent=(
                (position[0] + self.margin),
                (position[0] + receptacle_width + self.margin), 
                position[1], 
                (position[1] + receptacle_height + 20)
            )
        )

        self.center_position = (position[0] + self.width / 2, position[1] + self.height / 2)  # Update center position
        self.top_position = (position[0] + self.width / 2, position[1] + self.height)  # Update top position

        # Wrap the text if it's longer than a certain length
        wrapped_text = textwrap.fill(self.receptacle_id, width=10)

        ax.annotate(wrapped_text, 
                    xy=((position[0] + self.width / 2), position[1]),  # Use center position for annotation
                    ha='center', va='top', color='black', fontsize=int(os.environ['receptacle_text_size']))
        
        ax.axis('off')

        if created_fig:
            return fig, ax
        else:
            return ax