import os
import json
import re
import shutil
from bs4 import BeautifulSoup
from urllib.parse import unquote

SITE_ROOT = '/home/daniel/imgur/sites/nutrisalud.com.es'
ARTICLES_DIR = os.path.join(SITE_ROOT, 'articulos')
IMAGES_DIR = os.path.join(SITE_ROOT, 'images')

# Mapping from user request (filtered for existing files)
seo_data = [
    {"file": "gominolas-vinagre-manzana.html", "keywords": ["gominolas de vinagre de manzana"]},
    {"file": "triple-magnesio.html", "keywords": ["triple magnesio"]},
    {"file": "hoja-morera.html", "keywords": ["hoja de morera"]},
    {"file": "gochugaru.html", "keywords": ["gochugaru"]},
    {"file": "chocolates-almendras.html", "keywords": ["chocolates con almendras"]},
    {"file": "fecula-maiz.html", "keywords": ["fécula de maíz"]},
    {"file": "nucita.html", "keywords": ["nucita"]},
    {"file": "orujo-hierbas.html", "keywords": ["orujo de hierbas"]},
    {"file": "shatavari.html", "keywords": ["shatavari"]},
    {"file": "malato-magnesio.html", "keywords": ["malato de magnesio"]},
    {"file": "aloclair.html", "keywords": ["aloclair"]},
    {"file": "paniculata.html", "keywords": ["paniculata"]},
    {"file": "tktx.html", "keywords": ["tktx"]},
    {"file": "hondrofrost.html", "keywords": ["hondrofrost"]},
    {"file": "hondrodox.html", "keywords": ["hondrodox"]},
    {"file": "hondro-sol.html", "keywords": ["hondro sol"]},
    {"file": "crema-veneno-abeja.html", "keywords": ["crema con veneno de abeja"]}
]

# Track processed images to avoid renaming the same file multiple times if shared
processed_images = set()

def clean_filename(name):
    # Remove extension
    base, ext = os.path.splitext(name)
    # Remove dots and weird chars from base
    base = re.sub(r'[^a-zA-Z0-9\s\-_]', '', base)
    return base, ext

def slugify(text):
    text = text.lower()
    text = re.sub(r'[áàäâ]', 'a', text)
    text = re.sub(r'[éèëê]', 'e', text)
    text = re.sub(r'[íìïî]', 'i', text)
    text = re.sub(r'[óòöô]', 'o', text)
    text = re.sub(r'[úùüû]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def update_references_in_all_files(old_name, new_name):
    # Relies on unique filenames
    print(f"  Updating references: {old_name} -> {new_name}")
    for root, dirs, files in os.walk(SITE_ROOT):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if old_name in content:
                    # Simple string replace is risky if names are subsets, but with image filenames usually okay
                    # We usually look for 'images/old_name' or Just old_name?
                    # Let's try to be specific to avoid replacing text
                    # We'll replace the filename part only
                    new_content = content.replace(old_name, new_name)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

for item in seo_data:
    filename = item['file']
    keyword = item['keywords'][0] # Use primary keyword
    file_path = os.path.join(ARTICLES_DIR, filename)
    
    if not os.path.exists(file_path):
        print(f"Skipping {filename} (not found)")
        continue

    print(f"Processing {filename}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    images = soup.find_all('img')
    keyword_slug = slugify(keyword)
    
    count = 1
    files_changed = False
    
    for img in images:
        src = img.get('src')
        if not src or src.startswith('http'):
            continue
            
        # Resolving path based on ../images/ usually in articles
        # or images/ in other pages. We assume articles are in /articulos/ so path is ../images/filename.ext
        
        img_filename = os.path.basename(src)
        
        if img_filename in processed_images:
            continue
            
        # Check if actual file exists
        full_img_test_path = os.path.join(IMAGES_DIR, img_filename)
        if not os.path.exists(full_img_test_path):
            print(f"  Image not found on disk: {img_filename}")
            continue

        # Determine new name
        # Strategy: keyword-slug + original_meaningful_parts + counter
        base_orig, ext = clean_filename(img_filename)
        
        # Avoid double slugging if already optimized
        if keyword_slug in base_orig and '-' in base_orig:
             new_base = base_orig # Already has keyword
        else:
             # Try to keep some original context if it's not just "image1"
             # e.g. "shatavari_powder_spoon" -> "shatavari-powder-spoon"
             # If keyword is "shatavari", we just normalize.
             
             # If the filename is completely different, append
             # e.g. "melting_dark_chocolate" + keyword "chocolates con almendras"
             # -> "chocolates-con-almendras-melting-dark-chocolate"
             
             clean_base_slug = slugify(base_orig)
             if clean_base_slug.startswith(keyword_slug):
                 new_base = clean_base_slug
             else:
                 new_base = f"{keyword_slug}-{clean_base_slug}"
        
        # Ensure max length reasonable
        if len(new_base) > 80:
            new_base = new_base[:80]
            
        new_filename = f"{new_base}{ext}"
        
        # If name changed, rename file
        if new_filename != img_filename:
            try:
                os.rename(os.path.join(IMAGES_DIR, img_filename), os.path.join(IMAGES_DIR, new_filename))
                processed_images.add(new_filename)
                
                # Update ALL references
                update_references_in_all_files(img_filename, new_filename)
                
                # Update current variable to reflect change for Alt text step
                img['src'] = img['src'].replace(img_filename, new_filename)
                files_changed = True
                print(f"  Renamed: {img_filename} -> {new_filename}")
            except OSError as e:
                print(f"  Error renaming {img_filename}: {e}")
                processed_images.add(img_filename)
        else:
            processed_images.add(img_filename)

        # Update Alt Text
        alt = img.get('alt', '')
        if keyword.lower() not in alt.lower():
            # append keyword nicely
            if alt:
                img['alt'] = f"{alt} - {keyword}"
            else:
                img['alt'] = f"{keyword} imagen"
            files_changed = True
            print(f"  Updated ALT: {img['alt']}")
            
    if files_changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

print("Optimization complete.")
