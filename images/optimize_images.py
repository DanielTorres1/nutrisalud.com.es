#!/usr/bin/python3
import os
import argparse
from PIL import Image

def optimize_images(directory):
    """Optimize images in the specified directory by resizing and converting to WebP."""
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory")
        return
    
    processed = 0
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filepath = os.path.join(directory, filename)
            try:
                with Image.open(filepath) as img:
                    # Resize if too large
                    max_width = 800
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Convert to WebP
                    new_filename = os.path.splitext(filename)[0] + '.webp'
                    new_filepath = os.path.join(directory, new_filename)
                    
                    img.save(new_filepath, 'WEBP', quality=85)
                    
                    print(f"Optimized: {filename} -> {new_filename} ({img.width}x{img.height})")
                    processed += 1
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    print(f"\nTotal images processed: {processed}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Optimize images by resizing and converting to WebP format.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--path',
        type=str,
        required=True,
        help='Path to the directory containing images to optimize'
    )
    
    args = parser.parse_args()
    
    print(f"Optimizing images in: {args.path}\n")
    optimize_images(args.path)
