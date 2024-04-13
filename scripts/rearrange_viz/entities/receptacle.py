import os
import matplotlib.pyplot as plt
from PIL import Image, ImageOps, ImageChops
import textwrap
from .constants import receptacle_properties, receptacle_color_map
from matplotlib.patches import FancyBboxPatch

class Receptacle:
    def __init__(self, receptacle_id, icon_path, scale=1.0):
        self.receptacle_id = receptacle_id
        self.icon_path = icon_path
        self.margin = 20
        self.center_placeholder_position = None  # Initialize center position
        self.top_placeholder_position = None  # Initialize top position
        self.placeholder_size = 40
        self.plot_placeholder = False
        self.init_size()

    def add_tint_to_rgb(self, image, tint_color):
        # Extract the alpha channel from the original image
        r, g, b, alpha = image.split()

        # Create a solid color image of the same size as the original image
        tint = Image.new('RGB', image.size, tint_color)

        # Composite the RGB channels with the tint color
        tinted_rgb = ImageChops.screen(tint.convert('RGB'), image.convert('RGB'))

        # Return the composite image with original alpha channel
        return Image.merge('RGBA', (tinted_rgb.split()[0], tinted_rgb.split()[1], tinted_rgb.split()[2], alpha))


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
        color = receptacle_color_map['_'.join(self.receptacle_id.split('_')[:-1])]
        color = tuple(int(255 * i) for i in color)
        icon = self.add_tint_to_rgb(icon, tint_color=color)
        receptacle_width, receptacle_height = icon.size
        ax.imshow(icon, 
            extent=(
                (position[0] + self.margin),
                (position[0] + receptacle_width + self.margin), 
                position[1], 
                (position[1] + receptacle_height + 20)
            )
        )

        self.center_placeholder_position = None
        self.top_placeholder_position = None
        if self.plot_placeholder:
            properties = receptacle_properties['_'.join(self.receptacle_id.split('_')[:-1])]
            if properties["is_on_top"]:
                self.top_placeholder_position = (position[0] + self.width / 2, position[1] + self.height + 25)  # Update top position
                object_rect = FancyBboxPatch(
                    (self.top_placeholder_position[0] - self.placeholder_size/2, self.top_placeholder_position[1] - self.placeholder_size/2),
                    self.placeholder_size, 
                    self.placeholder_size, 
                    edgecolor='white', 
                    facecolor='black', 
                    linewidth=0, 
                    linestyle='-', 
                    boxstyle='Round, pad=0, rounding_size=4', 
                    alpha=1.0, 
                )

                ax.add_patch(object_rect)
                
            if properties["is_inside"]:
                self.center_placeholder_position = (position[0] + self.width / 2, position[1] + self.height / 2)  # Update center position
                object_rect = FancyBboxPatch(
                    (self.center_placeholder_position[0] - self.placeholder_size/2, self.center_placeholder_position[1] - self.placeholder_size/2),
                    self.placeholder_size, 
                    self.placeholder_size, 
                    edgecolor='white', 
                    facecolor='black', 
                    linewidth=0, 
                    linestyle='-', 
                    boxstyle='Round, pad=0, rounding_size=4', 
                    alpha=1.0, 
                )

                ax.add_patch(object_rect)
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