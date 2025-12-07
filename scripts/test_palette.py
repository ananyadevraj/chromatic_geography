"""
color extraction for Chromatic Geography.
uses ColorThief (median cut) to extract dominant colors from city photographs.
"""

import json
from pathlib import Path
from collections import Counter
from colorthief import ColorThief

IMAGES_DIR = Path("data/images/cities")
OUTPUT_DIR = Path("data/colors")
NUM_COLORS = 6


def rgb_to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def rgb_to_hsl(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_c, min_c = max(r, g, b), min(r, g, b)
    diff = max_c - min_c
    l = (max_c + min_c) / 2
    
    if diff == 0:
        return (0, 0, l * 100)
    
    s = diff / (2 - max_c - min_c) if l > 0.5 else diff / (max_c + min_c)
    
    if max_c == r:
        h = ((g - b) / diff) % 6
    elif max_c == g:
        h = (b - r) / diff + 2
    else:
        h = (r - g) / diff + 4
    
    return (h * 60, s * 100, l * 100)


def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def filter_colors(colors, max_browns=2):
    filtered = []
    brown_count = 0
    
    for rgb in colors:
        h, s, l = rgb_to_hsl(*rgb)
        
        if l < 15 or l > 85:
            continue
        if s < 20:
            continue
        if s < 30 and 25 < l < 75:
            continue
        
        is_brown = (15 <= h <= 45) and (s < 55) and (25 < l < 65)
        if is_brown:
            if brown_count >= max_browns:
                continue
            brown_count += 1
        
        filtered.append(rgb)
    
    if not filtered:
        return sorted(colors, key=lambda c: rgb_to_hsl(*c)[1], reverse=True)
    
    return sorted(filtered, key=lambda c: rgb_to_hsl(*c)[1], reverse=True)


def ensure_diversity(colors, min_distance=30):
    if not colors:
        return colors
    
    diverse = [colors[0]]
    for color in colors[1:]:
        if all(color_distance(color, sel) > min_distance for sel in diverse):
            diverse.append(color)
    return diverse


def extract_colors(image_path, num_colors=6):
    ct = ColorThief(str(image_path))
    palette = ct.get_palette(color_count=num_colors + 10, quality=1)
    filtered = filter_colors(palette, max_browns=2)
    diverse = ensure_diversity(filtered)
    return [rgb_to_hex(*c) for c in diverse[:num_colors]]


def process_city(city_name):
    city_dir = IMAGES_DIR / city_name
    if not city_dir.exists():
        return None
    
    images = list(city_dir.glob("*.jpg")) + list(city_dir.glob("*.png"))
    if not images:
        return None
    
    print(f"{city_name}: {len(images)} images")
    
    all_palettes = []
    all_colors = []
    
    for img in images:
        try:
            colors = extract_colors(img, NUM_COLORS)
            all_palettes.append({"image": img.name, "colors": colors})
            all_colors.extend(colors)
        except Exception as e:
            print(f"  failed: {img.name}")
    
    color_counts = Counter(all_colors)
    top_colors = [color for color, _ in color_counts.most_common(NUM_COLORS)]
    
    return {
        "city": city_name,
        "image_count": len(images),
        "individual_palettes": all_palettes,
        "aggregated_palette": top_colors
    }


def main():
    if not IMAGES_DIR.exists():
        print(f"Images directory not found: {IMAGES_DIR}")
        return
    
    cities = [d.name for d in IMAGES_DIR.iterdir() if d.is_dir()]
    if not cities:
        print(f"No city directories found in {IMAGES_DIR}")
        return
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for city in cities:
        data = process_city(city)
        if data:
            output_path = OUTPUT_DIR / f"{city}_colors.json"
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  saved: {output_path}")


if __name__ == "__main__":
    main()