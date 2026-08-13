import zipfile
import re
from pathlib import Path
from bs4 import BeautifulSoup

books = [
    "Delias Cakes{Smith, Delia}(2014, Hodder &amp_ Stoughton){112392336} libgen.li.epub",
    "Grigson, Jane - Good Things (2008, Grub Street Cookery) - libgen.li.epub",
    "Jamie Oliver - Everyday Super Food (2015, Ecco) - libgen.li.epub",
    "Jamie Oliver - Veg.epub",
    "Mallmann, Francis_ Kaminsky, Peter - Seven Fires_ Grilling the Argentine Way (2009, Artisan) - libgen.li.epub",
    "Medrich, Alice - Cocolat_ extraordinary chocolate desserts (2017, Dover Publications) - libgen.li.epub",
    "Nigel Slater - The Kitchen Diaries (2006, Fourth Estate Ltd) - libgen.li.epub",
    "Nigella Lawson - How To Eat_ The Pleasures and Principles of Good Food (2014, Vintage Digital) - libgen.li.epub",
    "Nigella Lawson - How to be a domestic goddess.epub",
]

def find_recipe_pages(z, sample=3):
    htmls = [n for n in z.namelist() if n.endswith(('.html', '.xhtml', '.htm'))]
    hits = []
    for h in htmls:
        txt = z.read(h).decode('utf-8', errors='ignore')
        soup = BeautifulSoup(txt, 'html.parser')
        text = soup.get_text(' ', strip=True)
        # strong recipe signal
        if re.search(r'(?i)ingredients', text) and len(text) > 300:
            hits.append((h, soup, text))
            if len(hits) >= sample:
                break
    return hits

for book in books:
    p = Path("books") / book
    if not p.exists():
        print(f"MISSING: {book}")
        continue
    print(f"\n{'='*70}\n{book}\n{'='*70}")
    with zipfile.ZipFile(p, 'r') as z:
        hits = find_recipe_pages(z, sample=2)
        if not hits:
            print("No recipe pages found")
            continue
        for h, soup, text in hits:
            print(f"\n--- {h} ---")
            print(text[:1200])
            print("\n[HTML]\n")
            print(str(soup)[:3000])
