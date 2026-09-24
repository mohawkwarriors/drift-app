import os
from PIL import Image, ImageDraw

def make_squircle(image, size, radius_ratio=0.225):
    """Resizes image and applies squircle alpha mask."""
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
        print("Error: No source icon found. Please place 'icon.png' in the project root.")
        exit(1)

    print(f"Using source icon: {src_icon}")
    base_img = Image.open(src_icon).convert("RGBA")
    bg_color = (13, 15, 24, 255)  # #0d0f18 Drift Dark Celestial Background

    # -------------------------------------------------------------
    # 1. WEB / PWA ICONS
    # -------------------------------------------------------------
    # Full-bleed squircle icons for standard web contexts & desktop
    make_squircle(base_img, 192).save("android-chrome-192x192.png", "PNG")
    make_squircle(base_img, 512).save("android-chrome-512x512.png", "PNG")

    # iOS Apple Touch Icon (180x180, iOS handles squircle clipping)
    base_img.resize((180, 180), Image.Resampling.LANCZOS).save("apple-touch-icon.png", "PNG")

    # PWA Maskable icons (padded with app background color so circular masking doesn't letterbox)
    for size in [192, 512]:
        canvas = Image.new("RGBA", (size, size), bg_color)
        inner_side = int(size * 0.72)
        inner_logo = base_img.resize((inner_side, inner_side), Image.Resampling.LANCZOS)
        offset = (size - inner_side) // 2
        canvas.paste(inner_logo, (offset, offset), inner_logo)
        canvas.save(f"icon-maskable-{size}.png", "PNG")

    print("Generated Web PWA icons.")

    # -------------------------------------------------------------
    # 2. ANDROID NATIVE / CAPACITOR ICONS
    # -------------------------------------------------------------
    res_dir = "android/app/src/main/res"
    if os.path.exists(res_dir):
        densities = {
            "mipmap-mdpi": (48, 108),
            "mipmap-hdpi": (72, 162),
            "mipmap-xhdpi": (96, 216),
            "mipmap-xxhdpi": (144, 324),
            "mipmap-xxxhdpi": (192, 432),
        }

        for folder, (legacy_size, fg_size) in densities.items():
            target_dir = os.path.join(res_dir, folder)
            os.makedirs(target_dir, exist_ok=True)

            # Legacy icons (used if launcher doesn't support adaptive icons)
            legacy_sq = make_squircle(base_img, legacy_size)
            legacy_sq.save(os.path.join(target_dir, "ic_launcher.png"), "PNG")
            legacy_sq.save(os.path.join(target_dir, "ic_launcher_round.png"), "PNG")

            # Adaptive icon foreground (logo centered at safe-zone scale 66%)
            fg = Image.new("RGBA", (fg_size, fg_size), (0, 0, 0, 0))
            inner_side = int(fg_size * 0.66)
            inner_logo = base_img.resize((inner_side, inner_side), Image.Resampling.LANCZOS)
            offset = (fg_size - inner_side) // 2
            fg.paste(inner_logo, (offset, offset), inner_logo)
            fg.save(os.path.join(target_dir, "ic_launcher_foreground.png"), "PNG")

        # Set adaptive icon background to #0d0f18 instead of transparent
        values_dir = os.path.join(res_dir, "values")
        os.makedirs(values_dir, exist_ok=True)
        with open(os.path.join(values_dir, "ic_launcher_background.xml"), "w") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#0d0f18</color>\n</resources>\n')

        # Adaptive icon XML configs
        anydpi_dir = os.path.join(res_dir, "mipmap-anydpi-v26")
        os.makedirs(anydpi_dir, exist_ok=True)
        adaptive_xml = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
            '    <background android:drawable="@color/ic_launcher_background"/>\n'
            '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
            '</adaptive-icon>\n'
        )
        with open(os.path.join(anydpi_dir, "ic_launcher.xml"), "w") as f:
            f.write(adaptive_xml)
        with open(os.path.join(anydpi_dir, "ic_launcher_round.xml"), "w") as f:
            f.write(adaptive_xml)

        print("Generated Android Adaptive icons with #0d0f18 background.")

if __name__ == "__main__":
    build_all_icons()
