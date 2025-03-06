#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate basic icons for SITG Video Trimmer
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, bg_color, fg_color, text=None, save_path=None):
    """Create a basic icon with optional text."""
    img = Image.new('RGBA', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a film strip design
    width, height = size
    strip_height = height // 8
    
    for i in range(0, height, strip_height * 2):
        draw.rectangle([(0, i), (width, i + strip_height)], fill=fg_color)
    
    # Draw a play triangle in the center
    center_x, center_y = width // 2, height // 2
    triangle_size = min(width, height) // 3
    
    draw.polygon([
        (center_x - triangle_size // 2, center_y - triangle_size // 2),
        (center_x - triangle_size // 2, center_y + triangle_size // 2),
        (center_x + triangle_size // 2, center_y)
    ], fill=fg_color)
    
    # Add text if provided
    if text:
        try:
            font = ImageFont.truetype("arial.ttf", size=width // 10)
        except IOError:
            font = ImageFont.load_default()
        
        # Use textbbox instead of textsize (which is deprecated)
        try:
            # For newer Pillow versions
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except AttributeError:
            # Fallback for older Pillow versions
            text_width, text_height = draw.textsize(text, font=font)
        
        draw.text(
            (width // 2 - text_width // 2, height - text_height - 10),
            text,
            fill=fg_color,
            font=font
        )
    
    # Save the image if a path is provided
    if save_path:
        img.save(save_path)
    
    return img

def main():
    """Generate all icons for the application."""
    # Create the assets directory if it doesn't exist
    assets_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the main application icon
    create_icon(
        (256, 256),
        (50, 50, 50, 255),
        (200, 200, 200, 255),
        "SITG",
        os.path.join(assets_dir, "icon.png")
    )
    
    # Create ICO format for Windows
    icon = create_icon(
        (256, 256),
        (50, 50, 50, 255),
        (200, 200, 200, 255),
        "SITG"
    )
    
    # Save in multiple sizes for ICO
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    
    for size in icon_sizes:
        icons.append(icon.resize(size, Image.LANCZOS))
    
    # Save as ICO
    icons[0].save(
        os.path.join(assets_dir, "icon.ico"),
        format="ICO",
        sizes=[(icon.width, icon.height) for icon in icons]
    )
    
    print("Icons generated successfully!")

if __name__ == "__main__":
    main()
