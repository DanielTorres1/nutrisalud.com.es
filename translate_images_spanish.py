import os
import re
from bs4 import BeautifulSoup
import unicodedata

SITE_ROOT = '/home/daniel/imgur/sites/nutrisalud.com.es'
ARTICLES_DIR = os.path.join(SITE_ROOT, 'articulos')
IMAGES_DIR = os.path.join(SITE_ROOT, 'images')

# Using the same list to ensure we cover all relevant pages
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

processed_images = set()

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
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
                    new_content = content.replace(old_name, new_name)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

for item in seo_data:
    filename = item['file']
    keyword = item['keywords'][0]
    file_path = os.path.join(ARTICLES_DIR, filename)
    
    if not os.path.exists(file_path):
        continue

    print(f"Processing {filename}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    images = soup.find_all('img')
    files_changed = False
    
    for img in images:
        src = img.get('src')
        if not src or src.startswith('http'):
            continue
            
        img_filename = os.path.basename(src)
        
        if img_filename in processed_images:
            continue
            
        full_img_test_path = os.path.join(IMAGES_DIR, img_filename)
        if not os.path.exists(full_img_test_path):
            print(f"  Image not found on disk: {img_filename}")
            continue

        base_orig, ext = os.path.splitext(img_filename)
        
        # USE ALT TEXT FOR NEW SPANISH NAME
        alt = img.get('alt', '')
        
        # If alt contains " - keyword" (added by previous script), clean it for slug if it makes it too repeating
        # But generally "alt" is a good description.
        
        # Fallback if no alt
        if not alt:
            alt = keyword
        
        new_base = slugify(alt)
        
        # If the generated slug is empty or too short, mix in keyword
        if len(new_base) < 5:
            new_base = slugify(f"{keyword}-{alt}")
            
        # Ensure max length
        if len(new_base) > 80:
            new_base = new_base[:80]
            
        new_filename = f"{new_base}{ext}"
        
        # If name matches old name, skip
        if new_filename != img_filename:
            try:
                # Check collision
                if os.path.exists(os.path.join(IMAGES_DIR, new_filename)):
                    # append random hash or counter if collision, but here lets assumes unique alts
                    # If collision is just "file already renamed" in another run, it's fine.
                    # But if different images mapped to same slug, we have issue.
                    # Append hash of old filename to be safe
                    import hashlib
                    hash_suffix = hashlib.md5(img_filename.encode()).hexdigest()[:4]
                    new_filename = f"{new_base}-{hash_suffix}{ext}"

                os.rename(os.path.join(IMAGES_DIR, img_filename), os.path.join(IMAGES_DIR, new_filename))
                processed_images.add(new_filename)
                
                # Update ALL references
                update_references_in_all_files(img_filename, new_filename)
                
                # Update soup
                img['src'] = img['src'].replace(img_filename, new_filename)
                files_changed = True
                print(f"  Renamed Spanish: {img_filename} -> {new_filename}")
            except OSError as e:
                print(f"  Error renaming {img_filename}: {e}")
                processed_images.add(img_filename)
        else:
            processed_images.add(img_filename)
            
    if files_changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))

print("Spanish translation complete.")
