import os
import shutil
from PIL import Image, ImageDraw

def make_squircle(image, size, radius_ratio=0.225):
    resized = image.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size, size)], radius=int(size * radius_ratio), fill=255)
    squircle = resized.copy()
    squircle.putalpha(mask)
    return squircle

def build_all_icons():
    candidates = [
        "icon.png",
        "icon_rounded.png",
        "android-chrome-512x512.png",
        "apple-touch-icon.png",
        "android-chrome-192x192.png",
        "www/icon.png"
    ]
    src_icon = next((f for f in candidates if os.path.exists(f)), None)

    if not src_icon:
        print("Error: No source icon found.")
        exit(1)

    print(f"Using source icon: {src_icon}")
    base_img = Image.open(src_icon).convert("RGBA")

    # 1. Web PWA Icons (Pure Squircles with transparent outside corners)
    make_squircle(base_img, 192).save("android-chrome-192x192.png", "PNG")
    make_squircle(base_img, 512).save("android-chrome-512x512.png", "PNG")
    base_img.resize((180, 180), Image.Resampling.LANCZOS).save("apple-touch-icon.png", "PNG")

    # 2. Android Native Mipmap Icons
    res_dir = "android/app/src/main/res"
    if os.path.exists(res_dir):
        # Remove adaptive icon XMLs so the launcher renders the squircle PNG directly
        anydpi_dir = os.path.join(res_dir, "mipmap-anydpi-v26")
        if os.path.exists(anydpi_dir):
            shutil.rmtree(anydpi_dir)
            print("Removed mipmap-anydpi-v26 to disable adaptive circle masking.")

        densities = {
            "mipmap-mdpi": 48,
            "mipmap-hdpi": 72,
            "mipmap-xhdpi": 96,
            "mipmap-xxhdpi": 144,
            "mipmap-xxxhdpi": 192,
        }

        for folder, size in densities.items():
            target_dir = os.path.join(res_dir, folder)
            os.makedirs(target_dir, exist_ok=True)
            sq = make_squircle(base_img, size)
            sq.save(os.path.join(target_dir, "ic_launcher.png"), "PNG")
            sq.save(os.path.join(target_dir, "ic_launcher_round.png"), "PNG")

        print("Generated native squircle PNG icons across all mipmap densities.")

if __name__ == "__main__":
    build_all_icons()
