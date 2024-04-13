import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


class Placeholder:
    def __init__(self):
        self.center_position = None

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


        object_rect = FancyBboxPatch(
            (position[0], position[1]), 
            self.width, 
            self.height, 
            edgecolor='white', 
            facecolor='black', 
            linewidth=0, 
            linestyle='-', 
            boxstyle='Round, pad=0, rounding_size=4', 
            alpha=1.0, 
        )

        ax.add_patch(object_rect)

        self.center_position = (position[0] + self.width / 2, position[1] + self.height / 2)  # Update center position
        
        if created_fig:
            return fig, ax
        else:
            return ax
        
