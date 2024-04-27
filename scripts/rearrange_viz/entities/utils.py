from PIL import Image, ImageChops


def add_tint_to_rgb(image, tint_color):
    # Extract the alpha channel from the original image
    r, g, b, alpha = image.split()

    # Create a solid color image of the same size as the original image
    tint = Image.new('RGB', image.size, tint_color)

    # Composite the RGB channels with the tint color
    tinted_rgb = ImageChops.screen(tint.convert('RGB'), image.convert('RGB'))

    # Return the composite image with original alpha channel
    return Image.merge('RGBA', (tinted_rgb.split()[0], tinted_rgb.split()[1], tinted_rgb.split()[2], alpha))
