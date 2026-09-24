import os
import shutil
from PIL import Image, ImageDraw

def make_hd_squircle(image, size, radius_ratio=0.225):
    """Generates high-definition squircle using 8x supersampling and Lanczos anti-aliasing."""
    scale = 8
    hi_size = size * scale
    hi_img = image.resize((hi_size, hi_size), Image.Resampling.LANCZOS)

    hi_mask = Image.new("L", (hi_size, hi_size), 0)
    draw = ImageDraw.Draw(hi_mask)
    radius = int(hi_size * radius_ratio)
    # Coordinate boundary (0 to hi_size - 1) ensures perfect symmetric bounds
    draw.rounded_rectangle([(0, 0), (hi_size - 1, hi_size - 1)], radius=radius, fill=255)

    hi_img.putalpha(hi_mask)
    return hi_img.resize((size, size), Image.Resampling.LANCZOS)

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

    # 1. Web PWA Icons (High-definition anti-aliased squircles)
    make_hd_squircle(base_img, 192).save("android-chrome-192x192.png", "PNG", optimize=True)
    make_hd_squircle(base_img, 512).save("android-chrome-512x512.png", "PNG", optimize=True)
    make_hd_squircle(base_img, 180).save("apple-touch-icon.png", "PNG", optimize=True)

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
            sq = make_hd_squircle(base_img, size)
            sq.save(os.path.join(target_dir, "ic_launcher.png"), "PNG", optimize=True)
            sq.save(os.path.join(target_dir, "ic_launcher_round.png"), "PNG", optimize=True)

        print("Generated HD native squircle PNG icons across all mipmap densities.")

if __name__ == "__main__":
    build_all_icons()
