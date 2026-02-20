from PIL import Image, ImageSequence
import os
import sys

def webp_to_mp4_sequence(input_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    img = Image.open(input_path)
    for i, frame in enumerate(ImageSequence.Iterator(img)):
        frame.convert('RGB').save(f"{output_folder}/frame_{i:04d}.png")
    print(f"Extracted {i+1} frames.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_webp.py <input.webp> <output_folder>")
    else:
        webp_to_mp4_sequence(sys.argv[1], sys.argv[2])
