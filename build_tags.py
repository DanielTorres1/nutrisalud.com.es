import os
import re
from bs4 import BeautifulSoup

BASE_DIR = '/home/daniel/imgur/sites/nutrisalud.com.es'
ARTICLES_DIR = os.path.join(BASE_DIR, 'articulos')
TAGS_DIR = os.path.join(BASE_DIR, 'tags')

if not os.path.exists(TAGS_DIR):
    os.makedirs(TAGS_DIR)

tags_map = {}

# 1. Scan articles
print("Scanning articles for tags...")
for filename in os.listdir(ARTICLES_DIR):
    if not filename.endswith('.html'):
        continue
    
    filepath = os.path.join(ARTICLES_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    # Extract Tags
    article_tags = set()
    # Look for spans containing '#' or lines with text containing '#'
    # We specifically look into article-meta or just scan all text nodes for #Word
    
    # Strategy: Find all text nodes, regex search for #Tag.
    # To be safer and avoid extracting CSS/JS, we stick to body text.
    body_content = soup.find('body')
    if body_content:
        text_content = body_content.get_text()
        # However, getting all text might merge heavy text.
        # Let's stick to the convention seen: spans or meta divs usually hold these.
        # Let's search in all elements, but specifically look for the #Char pattern.
        # Better: Look for the specific meta block or just regex the whole raw file for simpler extraction if structure varies.
        # Actually BS4 is safer. Let's iterate over ALL string elements.
        for string in soup.stripped_strings:
            if '#' in string:
                found = re.findall(r'#([a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+)', string)
                for tag in found:
                    # Filter out hex colors just in case (though unlikely in visible text)
                    if len(tag) == 6 and all(c in '0123456789abcdefABCDEF' for c in tag):
                        continue # Skip potential hex codes if they appear in text (rare but possible)
                    article_tags.add(tag)
    
    if not article_tags:
        continue

    # Extract Meta
    # Prefer H1 inside article-header or main article content
    article_h1 = None
    
    # Try article-header first (standard in this site)
    header_div = soup.find('div', class_='article-header')
    if header_div:
        article_h1 = header_div.find('h1')
    
    # Try finding any H1 that is not the logo
    if not article_h1:
        for h in soup.find_all('h1'):
            # The logo usually has class 'logo-icon' in a span inside, or text matches NutriSalud
            if h.find('span', class_='logo-icon'):
                continue
            if 'NutriSalud' in h.get_text() and len(h.get_text().strip()) < 20: 
                # Heuristic: Short title with NutriSalud is likely logo
                continue
            article_h1 = h
            break
            
    title = article_h1.get_text().strip() if article_h1 else filename
    
    # Excerpt
    excerpt = "Leer artículo..."
    # Try description meta tag first for a clean excerpt
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        excerpt = meta_desc['content']
    else:
        # Fallback to first p
        body_div = soup.find('div', class_='article-body')
        if body_div:
            p = body_div.find('p')
            if p:
                excerpt = p.get_text().strip()[:150] + "..."
    
    # Image
    image_src = "images/default_placeholder.webp"
    main_img = None
    
    # Try finding image in article-content
    content_div = soup.find('article', class_='article-content')
    if content_div:
        imgs = content_div.find_all('img')
        for img in imgs:
            # Skip logo icons or unrelated icons
            if 'logo-icon' in img.get('class', []):
                continue
            main_img = img['src']
            break
            
    if main_img:
        # Normalize path
        if '../images/' in main_img:
            image_src = main_img.replace('../images/', 'images/')
        elif main_img.startswith('images/'):
            image_src = main_img
        elif main_img.startswith('../'):
             # Handle other relative paths if any
             pass
    
    article_data = {
        'filename': filename,
        'title': title,
        'excerpt': excerpt,
        'image': image_src,
        'url': f'articulos/{filename}'
    }

    print(f"Found tags {article_tags} in {filename}")
    for tag in article_tags:
        if tag not in tags_map:
            tags_map[tag] = []
        tags_map[tag].append(article_data)

# 2. Generate Tag Pages
print("Generating tag pages...")

def generate_tag_page(tag_name, articles):
    safe_name = tag_name.lower()
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Artículos etiquetados com #{tag_name} en NutriSalud">
    <title>#{tag_name} - Artículos | NutriSalud</title>
    <link rel="stylesheet" href="../styles.css?v=2">
</head>
<body>
    <header>
        <div class="header-container">
            <div class="logo">
                <h1><span class="logo-icon">🥗</span> NutriSalud</h1>
            </div>
            <nav>
                <ul>
                    <li><a href="../recetas.html">Recetas</a></li>
                    <li><a href="../suplementos.html">Suplementos</a></li>
                    <li><a href="../cremas-topicas.html">Cremas</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <div class="container">
        <div class="breadcrumbs">
            <a href="../index.html">Inicio</a> <span>›</span> <strong>#{tag_name}</strong>
        </div>

        <h1>🏷️ Tema: #{tag_name}</h1>
        <p class="mb-lg">Recetas, suplementos y artículos relacionados con <strong>{tag_name}</strong>.</p>

        <div class="article-grid">
"""
    
    for art in articles:
        img_rel = "../" + art['image']
        link_rel = "../" + art['url']
        
        html_content += f"""
            <a href="{link_rel}" class="article-card">
                <div class="article-card-header">
                    <h3>{art['title']}</h3>
                </div>
                <img src="{img_rel}" alt="{art['title']}" class="article-card-image" loading="lazy">
                <div class="article-card-body">
                    <p class="excerpt">{art['excerpt']}</p>
                    <span class="read-more">Leer más →</span>
                </div>
            </a>
"""

    html_content += """
        </div>
    </div>

    <footer>
        <div class="footer-content">
            <p>&copy; 2024 NutriSalud.com.es - Todos los derechos reservados</p>
        </div>
    </footer>
</body>
</html>
"""
    
    with open(os.path.join(TAGS_DIR, f'{safe_name}.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

for tag, articles in tags_map.items():
    generate_tag_page(tag, articles)

# 3. Insert Tag Cloud in Index
print("Updating index.html with Tag Cloud...")
tag_cloud_html = f'''
        <section class="tag-cloud-section mt-lg" style="margin-bottom: 3rem;">
            <h2 class="text-center">Explora por Temas</h2>
            <div class="tag-cloud-container" style="display: flex; flex-wrap: wrap; justify-content: center; gap: 0.8rem; max-width: 800px; margin: 0 auto;">
'''

for tag in sorted(tags_map.keys()):
    safe_name = tag.lower()
    tag_cloud_html += f'                <a href="tags/{safe_name}.html" class="tag-pill" style="background-color: var(--pale-green); color: var(--dark-green); padding: 0.5rem 1.2rem; border-radius: 50px; text-decoration: none; font-weight: 600; font-size: 0.95rem; transition: transform 0.2s;">#{tag}</a>\n'

tag_cloud_html += '''            </div>
        </section>'''

index_path = os.path.join(BASE_DIR, 'index.html')
with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

# Remove old cloud if exists to avoid duplication during re-runs
index_content = re.sub(r'<section class="tag-cloud-section.*?</section>', '', index_content, flags=re.DOTALL)

# Insert before featured section
# Note: Cleaning up extra newlines might be needed
target_str = '<section class="featured-section'
if target_str in index_content:
    new_content = index_content.replace(target_str, tag_cloud_html + '\n\n        ' + target_str)
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Index updated successfully.")
else:
    print("Warning: Could not find insertion point 'featured-section' in index.html")

print("Done.")
