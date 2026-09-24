import os
from PIL import Image, ImageDraw

def make_squircle(image, size, radius_ratio=0.225):
    """Resizes image and applies rounded rectangle (squircle) alpha mask."""
    resized = image.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size, size)], radius=int(size * radius_ratio), fill=255)
    squircle = resized.copy()
    squircle.putalpha(mask)
    return squircle

def build_all_icons():
    # Detect high-res source icon
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
        print(f"Error: No source icon found. Please place 'icon.png' in the project root.")
        exit(1)

    print(f"Using source icon: {src_icon}")
    base_img = Image.open(src_icon).convert("RGBA")

    # -------------------------------------------------------------
    # 1. WEB / PWA ICONS (Written to project root)
    # -------------------------------------------------------------
    # Full-bleed squircles for standard / desktop / "any" purpose
    make_squircle(base_img, 192).save("android-chrome-192x192.png", "PNG")
    make_squircle(base_img, 512).save("android-chrome-512x512.png", "PNG")

    # Apple Touch Icon (180x180; iOS handles squircle mask automatically)
    base_img.resize((180, 180), Image.Resampling.LANCZOS).save("apple-touch-icon.png", "PNG")

    # Inset maskable icons (squircle scaled to 64% on transparent canvas)
    # Keeps squircle inside the 80% safe zone so Android's circle mask doesn't clip corners
    for size in [192, 512]:
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        inner_side = int(size * 0.64)
        inner_squircle = make_squircle(base_img, inner_side)
        offset = (size - inner_side) // 2
        canvas.paste(inner_squircle, (offset, offset), inner_squircle)
        canvas.save(f"icon-maskable-{size}.png", "PNG")

    print("Generated Web PWA icons (android-chrome-*.png, icon-maskable-*.png, apple-touch-icon.png).")

    # -------------------------------------------------------------
    # 2. ANDROID NATIVE / CAPACITOR ICONS (If android/ directory exists)
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

            # Legacy fallback icons
            legacy_sq = make_squircle(base_img, legacy_size)
            legacy_sq.save(os.path.join(target_dir, "ic_launcher.png"), "PNG")
            legacy_sq.save(os.path.join(target_dir, "ic_launcher_round.png"), "PNG")

            # Adaptive icon foreground: squircle sized at 54% of 108dp canvas
            fg = Image.new("RGBA", (fg_size, fg_size), (0, 0, 0, 0))
            inner_side = int(fg_size * 0.54)
            inner_squircle = make_squircle(base_img, inner_side)
            offset = (fg_size - inner_side) // 2
            fg.paste(inner_squircle, (offset, offset), inner_squircle)
            fg.save(os.path.join(target_dir, "ic_launcher_foreground.png"), "PNG")

        # Transparent adaptive icon background
        values_dir = os.path.join(res_dir, "values")
        os.makedirs(values_dir, exist_ok=True)
        with open(os.path.join(values_dir, "ic_launcher_background.xml"), "w") as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#00000000</color>\n</resources>\n')

        # Adaptive icon XML configs (API 26+)
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

        print("Generated Android Adaptive squircle icon drawables in android/app/src/main/res/.")
    else:
        print("Note: 'android/' folder not found locally. Android native icons will be generated during CI build.")

if __name__ == "__main__":
    build_all_icons()
