"""
=============================================================================
LESSON 3: COLOR EXTRACTION
=============================================================================

This script teaches you:
1. How k-means clustering works for color extraction
2. Loading and processing images with Pillow
3. Converting between color formats (RGB, HEX, HSL)
4. Batch processing multiple files
5. Filtering out "boring" colors (too dark, too light, too gray)

Run this with: python scripts/03_color_extraction.py
=============================================================================
"""

import os
import json
from pathlib import Path
from collections import Counter

# Pillow for image processing
from PIL import Image

# We'll implement k-means ourselves first to understand it,
# then show the easier library method


# =============================================================================
# CONFIGURATION
# =============================================================================

# Where are our images?
IMAGES_DIR = Path("data/images/cities")

# Where to save the extracted colors?
OUTPUT_DIR = Path("data/colors")

# How many colors to extract per image?
NUM_COLORS = 6

# Image processing settings
RESIZE_TO = 150  # Resize images to this width for faster processing
                 # (Color extraction doesn't need full resolution)


# =============================================================================
# COLOR CONVERSION UTILITIES
# =============================================================================

def rgb_to_hex(r, g, b):
    """
    Convert RGB values (0-255 each) to a hex string.
    
    Example: rgb_to_hex(255, 107, 107) → "#ff6b6b"
    
    The format string explained:
    - {:02x} means: format as hex (x), with at least 2 digits (02)
    - We do this for red, green, and blue
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color):
    """
    Convert hex string to RGB tuple.
    
    Example: hex_to_rgb("#ff6b6b") → (255, 107, 107)
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hsl(r, g, b):
    """
    Convert RGB to HSL (Hue, Saturation, Lightness).
    
    HSL is more intuitive for humans:
    - Hue: The "color" (0-360, like degrees on a color wheel)
    - Saturation: How "vivid" (0-100, gray to pure color)
    - Lightness: How "bright" (0-100, black to white)
    
    We use HSL to filter out boring colors.
    """
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c
    
    # Lightness
    l = (max_c + min_c) / 2
    
    if diff == 0:
        h = s = 0  # Gray, no hue or saturation
    else:
        # Saturation
        s = diff / (2 - max_c - min_c) if l > 0.5 else diff / (max_c + min_c)
        
        # Hue
        if max_c == r:
            h = ((g - b) / diff) % 6
        elif max_c == g:
            h = (b - r) / diff + 2
        else:
            h = (r - g) / diff + 4
        
        h = h * 60  # Convert to degrees
    
    return (h, s * 100, l * 100)


# =============================================================================
# K-MEANS IMPLEMENTATION (Educational Version)
# =============================================================================

def color_distance(c1, c2):
    """
    Calculate the "distance" between two colors.
    
    We use Euclidean distance in RGB space:
    √((r1-r2)² + (g1-g2)² + (b1-b2)²)
    
    This isn't perceptually perfect (humans see green better than blue),
    but it's simple and works well enough.
    """
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def find_closest_centroid(pixel, centroids):
    """
    Find which centroid (cluster center) a pixel is closest to.
    Returns the index of the closest centroid.
    """
    distances = [color_distance(pixel, c) for c in centroids]
    return distances.index(min(distances))


def calculate_centroid(pixels):
    """
    Calculate the average color of a group of pixels.
    This becomes the new center of the cluster.
    """
    if not pixels:
        return (128, 128, 128)  # Default gray if empty
    
    r = sum(p[0] for p in pixels) // len(pixels)
    g = sum(p[1] for p in pixels) // len(pixels)
    b = sum(p[2] for p in pixels) // len(pixels)
    
    return (r, g, b)


def kmeans_colors(pixels, k=5, max_iterations=20):
    """
    Extract k dominant colors using k-means clustering.
    
    This is the "manual" implementation so you understand the algorithm.
    In practice, you'd use a library (shown later).
    
    Args:
        pixels: List of (r, g, b) tuples
        k: Number of colors to extract
        max_iterations: Maximum rounds of refinement
    
    Returns:
        List of k (r, g, b) tuples representing dominant colors
    """
    import random
    
    # Step 1: Initialize centroids randomly from existing pixels
    # (Picking random pixels as starting points is called "Forgy initialization")
    centroids = random.sample(pixels, min(k, len(pixels)))
    
    for iteration in range(max_iterations):
        # Step 2: Assign each pixel to nearest centroid
        clusters = [[] for _ in range(k)]
        
        for pixel in pixels:
            closest = find_closest_centroid(pixel, centroids)
            clusters[closest].append(pixel)
        
        # Step 3: Calculate new centroids (average of each cluster)
        new_centroids = []
        for i, cluster in enumerate(clusters):
            if cluster:
                new_centroids.append(calculate_centroid(cluster))
            else:
                # Empty cluster - keep old centroid
                new_centroids.append(centroids[i])
        
        # Step 4: Check if centroids have stabilized
        if new_centroids == centroids:
            break
        
        centroids = new_centroids
    
    # Sort by cluster size (most common colors first)
    cluster_sizes = [(len(clusters[i]), centroids[i]) for i in range(k)]
    cluster_sizes.sort(reverse=True)
    
    return [c[1] for c in cluster_sizes]


# =============================================================================
# IMAGE PROCESSING
# =============================================================================

def load_and_prepare_image(image_path):
    """
    Load an image and prepare it for color extraction.
    
    We resize it smaller because:
    1. Faster processing (fewer pixels to analyze)
    2. Color extraction doesn't need detail
    3. Reduces noise from tiny variations
    """
    try:
        img = Image.open(image_path)
        
        # Convert to RGB (in case it's RGBA, grayscale, etc.)
        img = img.convert('RGB')
        
        # Resize proportionally
        ratio = RESIZE_TO / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        return img
    
    except Exception as e:
        print(f"   ❌ Error loading {image_path}: {e}")
        return None


def get_pixels(img):
    """
    Extract all pixels from an image as a list of RGB tuples.
    """
    return list(img.getdata())


def filter_boring_colors(colors, strict=True, max_browns=2):
    """
    Remove colors that are too dark, too light, or too gray.
    Also limits the number of brown/earth tones to keep palettes vibrant.
    
    These "boring" colors don't tell us much about a city's character.
    We use HSL to make these judgments.
    
    Args:
        colors: List of RGB tuples
        strict: If True, use aggressive filtering (recommended)
        max_browns: Maximum number of brown/earth tones allowed
    """
    filtered = []
    brown_count = 0
    
    for rgb in colors:
        h, s, l = rgb_to_hsl(*rgb)
        
        if strict:
            # AGGRESSIVE FILTERING
            # Skip if:
            # - Too dark (lightness < 15%)
            # - Too light (lightness > 85%)
            # - Too gray (saturation < 20%)
            # - Gray zone: low saturation AND mid-lightness (the boring middle)
            
            if l < 15 or l > 85:
                continue
            if s < 20:
                continue
            # Extra filter: reject "muddy" colors (low-ish saturation + mid lightness)
            if s < 30 and 25 < l < 75:
                continue
            
            # BROWN LIMITING
            # Browns/earth tones typically have:
            # - Hue between 15-45 (orange-yellow range)
            # - Low to medium saturation (20-50%)
            # - Medium lightness (25-65%)
            is_brown = (15 <= h <= 45) and (s < 55) and (25 < l < 65)
            
            if is_brown:
                if brown_count >= max_browns:
                    continue  # Skip this brown, we have enough
                brown_count += 1
        else:
            # LENIENT FILTERING (old behavior)
            if l < 10 or l > 90:
                continue
            if s < 10:
                continue
        
        filtered.append(rgb)
    
    # If we filtered everything, return original but sorted by saturation
    if not filtered:
        # Sort by saturation (most colorful first) and return those
        sorted_by_sat = sorted(colors, key=lambda c: rgb_to_hsl(*c)[1], reverse=True)
        return sorted_by_sat
    
    # Sort by saturation to prioritize more vibrant colors
    filtered.sort(key=lambda c: rgb_to_hsl(*c)[1], reverse=True)
    
    return filtered


def ensure_color_diversity(colors, min_distance=30):
    """
    Ensure extracted colors are visually distinct.
    
    Sometimes k-means returns very similar colors.
    We filter out colors that are too close to each other.
    """
    if not colors:
        return colors
    
    diverse = [colors[0]]
    
    for color in colors[1:]:
        # Check if this color is far enough from all selected colors
        is_diverse = all(
            color_distance(color, selected) > min_distance 
            for selected in diverse
        )
        if is_diverse:
            diverse.append(color)
    
    return diverse


# =============================================================================
# MAIN EXTRACTION FUNCTION
# =============================================================================

def extract_colors_from_image(image_path, num_colors=5):
    """
    Extract dominant colors from a single image.
    
    Returns a list of hex color strings.
    """
    # Load image
    img = load_and_prepare_image(image_path)
    if img is None:
        return []
    
    # Get pixels
    pixels = get_pixels(img)
    
    # Extract MORE colors than we need (we'll filter many out)
    raw_colors = kmeans_colors(pixels, k=num_colors + 8)
    
    # Filter boring colors (grays, blacks, whites)
    filtered = filter_boring_colors(raw_colors, strict=True)
    
    # Ensure diversity
    diverse = ensure_color_diversity(filtered)
    
    # Take top N and convert to hex
    final_colors = diverse[:num_colors]
    hex_colors = [rgb_to_hex(*rgb) for rgb in final_colors]
    
    return hex_colors


# =============================================================================
# EASIER METHOD: Using ColorThief Library
# =============================================================================

def extract_colors_easy(image_path, num_colors=5):
    """
    Extract colors using the ColorThief library.
    
    This is much easier than our manual implementation!
    Install with: pip install colorthief
    
    ColorThief uses a more sophisticated algorithm called
    "Modified Median Cut Quantization" (MMCQ).
    """
    try:
        from colorthief import ColorThief
        
        ct = ColorThief(str(image_path))
        
        # Get MORE colors than needed so we can filter
        palette = ct.get_palette(color_count=num_colors + 10, quality=1)
        
        # Filter out boring grays/blacks/whites, limit browns to 2
        filtered = filter_boring_colors(palette, strict=True, max_browns=2)
        
        # Ensure diversity
        diverse = ensure_color_diversity(filtered)
        
        # Take top N
        final_colors = diverse[:num_colors]
        
        # Convert to hex
        hex_colors = [rgb_to_hex(*color) for color in final_colors]
        
        return hex_colors
    
    except ImportError:
        print("   ⚠️  ColorThief not installed. Using manual method.")
        return extract_colors_from_image(image_path, num_colors)
    except Exception as e:
        print(f"   ⚠️  ColorThief failed: {e}. Using manual method.")
        return extract_colors_from_image(image_path, num_colors)


# =============================================================================
# BATCH PROCESSING
# =============================================================================

def process_city(city_name):
    """
    Process all images for a single city.
    
    Returns a dictionary with:
    - Individual image palettes
    - Aggregated city palette
    """
    city_dir = IMAGES_DIR / city_name
    
    if not city_dir.exists():
        print(f"   ❌ Directory not found: {city_dir}")
        return None
    
    # Find all images
    image_files = list(city_dir.glob("*.jpg")) + list(city_dir.glob("*.png"))
    
    if not image_files:
        print(f"   ❌ No images found in {city_dir}")
        return None
    
    print(f"\n🏙️  Processing {city_name.upper()}: {len(image_files)} images")
    
    # Extract colors from each image
    all_palettes = []
    all_colors = []  # For aggregation
    
    for i, img_path in enumerate(image_files, 1):
        print(f"   [{i}/{len(image_files)}] {img_path.name}...", end=" ")
        
        # Use the easy method (ColorThief)
        colors = extract_colors_easy(img_path, NUM_COLORS)
        
        if colors:
            print(f"✅ {colors[0]}...")
            all_palettes.append({
                "image": img_path.name,
                "colors": colors
            })
            all_colors.extend(colors)
        else:
            print("❌ Failed")
    
    # Aggregate: Find the most common colors across all images
    color_counts = Counter(all_colors)
    top_colors = [color for color, count in color_counts.most_common(NUM_COLORS)]
    
    return {
        "city": city_name,
        "image_count": len(image_files),
        "individual_palettes": all_palettes,
        "aggregated_palette": top_colors
    }


def save_results(city_data):
    """
    Save extracted colors to JSON.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = OUTPUT_DIR / f"{city_data['city']}_colors.json"
    
    with open(output_path, 'w') as f:
        json.dump(city_data, f, indent=2)
    
    print(f"   💾 Saved to {output_path}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          CHROMATIC GEOGRAPHY - COLOR EXTRACTION           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  This script will:                                        ║
    ║  1. Load each downloaded image                            ║
    ║  2. Extract 5 dominant colors using k-means               ║
    ║  3. Filter out boring colors (too dark/light/gray)        ║
    ║  4. Save individual + aggregated palettes                 ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check if images directory exists
    if not IMAGES_DIR.exists():
        print(f"❌ Images directory not found: {IMAGES_DIR}")
        print("   Run the image scraper first (02_image_scraper.py)")
        return
    
    # Find all city directories
    cities = [d.name for d in IMAGES_DIR.iterdir() if d.is_dir()]
    
    if not cities:
        print(f"❌ No city directories found in {IMAGES_DIR}")
        return
    
    print(f"📁 Found {len(cities)} cities: {', '.join(cities)}")
    
    # Process each city
    all_results = {}
    
    for city in cities:
        city_data = process_city(city)
        
        if city_data:
            save_results(city_data)
            all_results[city] = city_data["aggregated_palette"]
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 COLOR EXTRACTION COMPLETE!")
    print("=" * 60)
    
    print("\n📊 Aggregated Palettes:")
    for city, palette in all_results.items():
        color_blocks = " ".join([f"[{c}]" for c in palette])
        print(f"   {city}: {color_blocks}")
    
    print(f"\n📁 Results saved to: {OUTPUT_DIR}/")
    
    print("""
    
Next steps:
1. Review the extracted palettes
2. Run the data processing script to prepare for D3
3. Build the frontend visualization
    """)


if __name__ == "__main__":
    main()