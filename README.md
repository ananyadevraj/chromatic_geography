# Chromatic Geography

A visual essay exploring the color palettes of 12 cities around the world, told through scrollytelling.

**[Explore the essay →](https://ananyadevraj.github.io/chromatic_geography/)**

## About

This project extracts dominant colors from 1,800 urban photographs (150 per city x 12 cities) and aggregates them into city-level color palettes.

Cities analyzed:
- Asia: Bangkok, Tokyo, Singapore, Jaipur 
- Europe: Istanbul, Copenhagen, Santorini 
- Africa: Marrakech 
- Oceania: Melbourne 
- North America: Havana, Mexico City
- South America: Rio de Janeiro

## Methodology

1. **Image collection** — Photographs pulled from Unsplash API
2. **Color extraction** — ColorThief library's Median Cut algorithm, which extracts 6 dominant colors per image
3. **Aggregation** — Frequency counting for the top 6 colors of the 150 images' color palettes for each city produces the aggregated city palette
4. **Analysis** — Temperature, saturation, contrast, and hue diversity calculated for each palette

## Findings

- **Warmest city**: Bangkok (76°)
- **Coolest city**: Santorini (24°)
- **Most similar pair**: Tokyo & Mexico City (both warm earth tones)
- **Most saturated**: Bangkok (79%) 
- **Most monochromatic**: Santorini (5/6 colors in blue family)
- **Only green-dominant city**: Singapore (4/6 colors) 

## Run locally

```bash
# Install dependencies
pip install colorthief pillow python-dotenv requests

# Add your Unsplash API key
echo "UNSPLASH_ACCESS_KEY=your_key_here" > .env

# Scrape images
python image_scraper.py

# Extract colors
python test_palette.py
```

## Files

```
index.html          # The visual essay
tokyo-temple.png    # image used as algorithm explanation example 
image_scraper.py    # Unsplash API scraper
color_extraction.py # ColorThief color extraction
```

## Credits

- Images: [Unsplash](https://unsplash.com)
- Color extraction: [ColorThief](https://github.com/fengsp/color-thief-py)
