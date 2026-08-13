

def _extract_delias_cakes_recipes(soup: BeautifulSoup, epub_path: str) -> List[Dict]:
    """Extract recipes from Delia's Cakes.

    Each recipe starts with a <p class="recipe-head"> title, followed by an
    optional intro (<p class="text-intro">), ingredient lines in
    recipe-text/recipe-text-top/recipe-text-bottom paragraphs, and method
    paragraphs in <p class="text-center"> (or a leading pre-heat paragraph).
    """
    recipes = []
    heads = soup.find_all('p', class_='recipe-head')
    for idx, head in enumerate(heads):
        title = _normalize_whitespace(head.get_text(' ', strip=True))
        if not title or len(title) < 3:
            continue

        ingredients = []
        steps = []
        in_steps = False

        for sib in head.find_next_siblings():
            cls = ' '.join(sib.get('class', []))
            # stop at the next recipe
            if sib.name == 'p' and 'recipe-head' in cls:
                break
            text = _normalize_whitespace(sib.get_text(' ', strip=True))
            if not text:
                continue
            # skip intro blurb
            if 'text-intro' in cls:
                continue
            # method paragraphs are text-center, or a leading pre-heat line
            if 'text-center' in cls:
                steps.append(text)
                in_steps = True
                continue
            # Once we see a recipe-text-bottom that starts like an instruction,
            # treat everything afterwards as steps.
            if 'recipe-text-bottom' in cls and in_steps:
                steps.append(text)
                continue
            # Ingredient lines live in recipe-text* paragraphs
            if any(c in cls for c in ('recipe-text', 'recipe-text-top', 'recipe-text-bottom')):
                low = text.lower()
                # subheadings like "For the filling:" or "To finish:"
                if low.startswith(('for the', 'to finish:')) or text.endswith(':'):
                    ingredients.append('--- ' + text)
                    continue
                # A lone "Preheat..." paragraph is the first method step.
                if re.match(r'^pre-?heat\s+', low) or \
                   (len(text) > 30 and any(low.startswith(v) for v in _STEP_VERBS) and
                    not _is_ingredient_line(text)):
                    in_steps = True
                    steps.append(text)
                    continue
                ingredients.append(text)
                continue

        if len(ingredients) < 2 or len(steps) < 1:
            continue

        recipes.append({
            'title': title,
            'ingredients': '\n'.join(ingredients).strip(),
            'steps': '\n'.join(steps).strip(),
            'source': os.path.basename(epub_path),
            'file_path': epub_path,
            'image': '',
        })

    return recipes


def _extract_good_things_recipes(soup: BeautifulSoup, epub_path: str) -> List[Dict]:
    """Best-effort extraction for Jane Grigson's 'Good Things'.

    Chapters begin with an <h1> title; individual recipes are <h2> headings
    (often italic French). Ingredients and method are embedded in paragraphs
    without semantic classes. We treat quantity-led paragraphs as ingredients
    and imperative-led paragraphs as steps.
    """
    recipes = []
    for h2 in soup.find_all('h2'):
        title = _normalize_whitespace(h2.get_text(' ', strip=True))
        if not title or len(title) < 4 or len(title) > 100:
            continue
        # Skip chapter/section headings (single short word, all-uppercase notes).
        words = title.split()
        if len(words) == 1 and len(title) < 12:
            continue
        if title.lower().startswith(('note', 'introduction', 'contents')):
            continue

        body = []
        for sib in h2.find_next_siblings():
            if sib.name in ('h1', 'h2'):
                break
            if sib.name != 'p':
                continue
            text = _normalize_whitespace(sib.get_text(' ', strip=True))
            if text:
                body.append(text)

        if len(body) < 3:
            continue

        # First body paragraph is often prose context; keep it as a step if it
        # doesn't look like an ingredient.
        ingredients = []
        steps = []
        for para in body:
            if _is_ingredient_line(para):
                ingredients.append(para)
            elif _is_step_line(para) or len(para) > 60:
                steps.append(para)
            else:
                # short, ambiguous lines are usually ingredients
                ingredients.append(para)

        if len(ingredients) < 2 or len(steps) < 1:
            continue

        recipes.append({
            'title': title,
            'ingredients': '\n'.join(ingredients).strip(),
            'steps': '\n'.join(steps).strip(),
            'source': os.path.basename(epub_path),
            'file_path': epub_path,
            'image': '',
        })

    return recipes


def _extract_everyday_super_food_recipes(soup: BeautifulSoup, epub_path: str) -> List[Dict]:
    """Extract recipes from Jamie Oliver's 'Everyday Super Food'.

    Each recipe page has an <h2> title, an optional health blurb in a
    .jamie_super_food_recipe_intro div, an <aside class="sidebar_wrapper">
    with a serves/time heading and ingredient paragraphs, and a
    <div class="maincontent_wrapper"> with method paragraphs.
    """
    recipes = []
    for title_tag in soup.find_all('h2'):
        title = _normalize_whitespace(title_tag.get_text(' ', strip=True))
        if not title or len(title) < 4 or len(title) > 120:
            continue
        # Section headings are short and lack a sidebar/maincontent wrapper nearby.
        sidebar = title_tag.find_next_sibling('aside', class_='sidebar_wrapper')
        if not sidebar:
            sidebar = title_tag.find_next('aside', class_='sidebar_wrapper')
        maincontent = title_tag.find_next_sibling('div', class_='maincontent_wrapper')
        if not maincontent:
            maincontent = title_tag.find_next('div', class_='maincontent_wrapper')
        if not (sidebar and maincontent):
            continue

        serves = ''
        h5 = sidebar.find('h5')
        if h5:
            serves = _normalize_whitespace(h5.get_text(' ', strip=True))

        ingredients = []
        for p in sidebar.find_all('p'):
            ing = _normalize_whitespace(p.get_text(' ', strip=True))
            if ing:
                ingredients.append(ing)

        steps = []
        for p in maincontent.find_all('p'):
            step = _normalize_whitespace(p.get_text(' ', strip=True))
            if step:
                steps.append(step)

        if len(ingredients) < 2 or len(steps) < 1:
            continue

        recipes.append({
            'title': title,
            'ingredients': '\n'.join(ingredients).strip(),
            'steps': '\n'.join(steps).strip(),
            'source': os.path.basename(epub_path),
            'file_path': epub_path,
            'image': '',
            'serves': serves,
        })

    return recipes


def _extract_jamie_veg_recipes(soup: BeautifulSoup, epub_path: str) -> List[Dict]:
    """Extract recipes from Jamie Oliver's 'Veg'.

    A recipe section has <h2 class="rec_head1"> title, an optional
    <h2 class="rec_subhead"> subtitle, <h5 class="serves">, a
    <section class="sidebar_wrapper"> with <ul class="ingredient_items">
    ingredient lines, and a <section class="maincontent_wrapper"> with
    method paragraphs.
    """
    recipes = []
    for title_tag in soup.find_all('h2', class_='rec_head1'):
        title = _normalize_whitespace(title_tag.get_text(' ', strip=True))
        if not title:
            continue
        subhead = title_tag.find_next_sibling('h2', class_='rec_subhead')
        if subhead:
            title += ' – ' + _normalize_whitespace(subhead.get_text(' ', strip=True))

        serves_tag = title_tag.find_next_sibling('h5', class_='serves')
        serves = _normalize_whitespace(serves_tag.get_text(' ', strip=True)) if serves_tag else ''

        sidebar = title_tag.find_next_sibling('section', class_='sidebar_wrapper')
        maincontent = title_tag.find_next_sibling('section', class_='maincontent_wrapper')
        if not (sidebar and maincontent):
            continue

        ingredients = []
        for li in sidebar.find_all('li'):
            ing = _normalize_whitespace(li.get_text(' ', strip=True))
            if ing:
                ingredients.append(ing)

        steps = []
        for p in maincontent.find_all('p'):
            step = _normalize_whitespace(p.get_text(' ', strip=True))
            if step:
                steps.append(step)

        if len(ingredients) < 2 or len(steps) < 1:
            continue

        recipes.append({
            'title': title,
            'ingredients': '\n'.join(ingredients).strip(),
            'steps': '\n'.join(steps).strip(),
            'source': os.path.basename(epub_path),
            'file_path': epub_path,
            'image': '',
            'serves': serves,
        })

    return recipes


def _extract_seven_fires_recipes(soup: BeautifulSoup, epub_path: str) -> List[Dict]:
    """Extract recipes from Francis Mallmann's 'Seven Fires'.

    Recipe pages use <p class="RH"> for the title, <p class="RHN"> for the
    subtitle/serves line, <p class="RI-M">/<p class="RI-L"> for ingredients,
    and <p class="TX">/<p class="TX1"> for method steps.
    """
    recipes = []
    for title_tag in soup.find_all('p', class_='RH'):
        title = _normalize_whitespace(title_tag.get_text(' ', strip=True))
        if not title or len(title) < 4 or len(title) > 120:
            continue

        serves = ''
        sub_tag = title_tag.find_next_sibling('p', class_='RHN')
        if sub_tag:
            serves = _normalize_whitespace(sub_tag.get_text(' ', strip=True))

        ingredients = []
        steps = []
        for sib in title_tag.find_next_siblings():
            cls = ' '.join(sib.get('class', []))
            if sib.name == 'p' and 'RH' in cls:
                break
            text = _normalize_whitespace(sib.get_text(' ', strip=True))
            if not text:
                continue
            if 'RI-' in cls:
                ingredients.append(text)
            elif 'TX' in cls or 'TXT' in cls:
                steps.append(text)
            elif 'RHN' in cls:
                serves += ' ' + text

        if len(ingredients) < 2 or len(steps) < 1:
            continue

        recipes.append({
            'title': title,
            'ingredients': '\n'.join(ingredients).strip(),
            'steps': '\n'.join(steps).strip(),
            'source': os.path.basename(epub_path),
            'file_path': epub_path,
            'image': '',
            'serves': serves.strip(),
        })

    return recipes


def _extract_cocolat_recipes(soup: BeautifulSoup, epub_path: str) -> List[Dict]:
    """Extract recipes from Alice Medrich's 'Cocolat'.

    Recipe titles are <h1 class="h1"> (chapter titles use <h1 class="h1p">).
    They are followed by a serves line in <p class="bkauthor">, an optional
    note in <p class="extract">, an "Ingredients:" block, numbered method
    steps, and optional "Special Equipment" lines.
    """
    recipes = []
    for title_tag in soup.find_all('h1', class_='h1'):
        if 'h1p' in ' '.join(title_tag.get('class', [])):
            continue
        title = _normalize_whitespace(title_tag.get_text(' ', strip=True))
        if not title or len(title) < 4 or len(title) > 100:
            continue

        serves = ''
        note = ''
        ingredients = []
        steps = []
        in_ingredients = False
        in_steps = False

        for sib in title_tag.find_next_siblings():
            if sib.name == 'h1' and 'h1' in ' '.join(sib.get('class', [])):
                break
            cls = ' '.join(sib.get('class', []))
            text = _normalize_whitespace(sib.get_text(' ', strip=True))
            if not text:
                continue

            if sib.name == 'h3' or 'Note' in text:
                # Notes/variations stop the recipe.
                if in_steps:
                    break
                continue

            if 'bkauthor' in cls:
                serves = text
                continue
            if 'extract' in cls:
                note = text
                continue

            # The "Ingredients:" marker itself is not useful text.
            if re.match(r'^ingredients:?\s*$', text, re.I):
                in_ingredients = True
                in_steps = False
                continue

            # Numbered steps mark the start of the method.
            if re.match(r'^\d+[\.\)]\s+', text):
                in_ingredients = False
                in_steps = True
                steps.append(text)
                continue

            if in_steps:
                steps.append(text)
            elif in_ingredients or _is_ingredient_line(text) or text.endswith(':'):
                in_ingredients = True
                # Keep subheadings like "Special Equipment:" or "For the ...:"
                if text.endswith(':') and not _is_ingredient_line(text):
                    ingredients.append('--- ' + text)
                else:
                    ingredients.append(text)
            else:
                # Prose that appears before numbered steps; include as note/step.
                if note:
                    note += ' ' + text
                else:
                    note = text

        if note and not steps:
            # Some recipes have entirely prose methods; keep them as steps.
            steps.append(note)

        if len(ingredients) < 2 or len(steps) < 1:
            continue

        recipes.append({
            'title': title,
            'ingredients': '\n'.join(ingredients).strip(),
            'steps': '\n'.join(steps).strip(),
            'source': os.path.basename(epub_path),
            'file_path': epub_path,
            'image': '',
            'serves': serves,
        })

    return recipes


def _extract_kitchen_diaries_recipes(soup: BeautifulSoup, epub_path: str) -> List[Dict]:
    """Extract recipes from Nigel Slater's 'The Kitchen Diaries'.

    Recipe titles are <h2 class="subhead2"> headings inside the diary pages.
    Ingredients live in <div class="recp"> (which may contain <p class="recp_txt">),
    method in the following <p class="none"> and <p class="normal"> paragraphs.
    <h2 class="subhead1"> marks diary date entries and stops a recipe.
    """
    recipes = []
    for title_tag in soup.find_all('h2'):
        cls = ' '.join(title_tag.get('class', []))
        if 'subhead2' not in cls:
            continue
        title = _normalize_whitespace(title_tag.get_text(' ', strip=True))
        if not title or len(title) < 4 or len(title) > 120:
            continue

        ingredients = []
        steps = []
        serves = ''

        for sib in title_tag.find_next_siblings():
            if sib.name == 'h2':
                break
            sib_cls = ' '.join(sib.get('class', []))
            text = _normalize_whitespace(sib.get_text(' ', strip=True))
            if not text:
                continue

            if 'recp' in sib_cls:
                # The div may already be split into recp_txt paragraphs, or it
                # may be a single block of text.
                txt_paras = sib.find_all('p', class_='recp_txt')
                if txt_paras:
                    for p in txt_paras:
                        line = _normalize_whitespace(p.get_text(' ', strip=True))
                        if line:
                            ingredients.append(line)
                else:
                    # split on the bullet character used in the book
                    for line in re.split(r'\s*[•·]\s+', text):
                        line = line.strip()
                        if line:
                            ingredients.append(line)
                continue

            if sib.name == 'p':
                low = text.lower()
                if low.startswith('enough for') or low.startswith('serves'):
                    serves += ' ' + text
                    continue
                # First paragraph after ingredients is usually the first step.
                if _is_step_line(text) or len(text) > 50:
                    steps.append(text)
                elif _is_ingredient_line(text):
                    ingredients.append(text)
                else:
                    steps.append(text)

        if len(ingredients) < 2 or len(steps) < 1:
            continue

        recipes.append({
            'title': title,
            'ingredients': '\n'.join(ingredients).strip(),
            'steps': '\n'.join(steps).strip(),
            'source': os.path.basename(epub_path),
            'file_path': epub_path,
            'image': '',
            'serves': serves.strip(),
        })

    return recipes


def _extract_nigella_how_to_eat_recipes(soup: BeautifulSoup, epub_path: str) -> List[Dict]:
    """Extract recipes from Nigella Lawson's 'How to Eat'.

    Recipes are marked by <h2 class="recipes-head"> titles. Ingredients follow
    in <p class="recipes-para"> / <p class="recipes-para1"> / <p class="recipes-paraa">
    paragraphs; method steps are in <p class="flush-lefts"> / <p class="indenteds">
    paragraphs. Chapter/section headings use <h2 class="chapter-head">.
    """
    recipes = []
    for title_tag in soup.find_all('h2', class_='recipes-head'):
        title = _normalize_whitespace(title_tag.get_text(' ', strip=True))
        if not title or len(title) < 4 or len(title) > 120:
            continue

        ingredients = []
        steps = []
        serves = ''

        for sib in title_tag.find_next_siblings():
            if sib.name == 'h2':
                cls = ' '.join(sib.get('class', []))
                if 'recipes-head' in cls or 'chapter-head' in cls:
                    break
            if sib.name != 'p':
                continue
            cls = ' '.join(sib.get('class', []))
            text = _normalize_whitespace(sib.get_text(' ', strip=True))
            if not text:
                continue

            if any(c in cls for c in ('recipes-para', 'recipes-para1', 'recipes-paraa')):
                # Some ingredient paragraphs contain section subheadings like
                # "CHICKEN WITH MORELS" that are not ingredients.
                if text.isupper() and len(text) < 60:
                    ingredients.append('--- ' + text)
                else:
                    ingredients.append(text)
            elif any(c in cls for c in ('flush-lefts', 'indenteds', 'indented', 'flush-left')):
                if _is_serves_line(text):
                    serves += ' ' + text
                else:
                    steps.append(text)
            else:
                # Ambiguous trailing paragraphs; keep if they look like steps.
                if _is_step_line(text):
                    steps.append(text)

        if len(ingredients) < 2 or len(steps) < 1:
            continue

        recipes.append({
            'title': title,
            'ingredients': '\n'.join(ingredients).strip(),
            'steps': '\n'.join(steps).strip(),
            'source': os.path.basename(epub_path),
            'file_path': epub_path,
            'image': '',
            'serves': serves.strip(),
        })

    return recipes


def _extract_nigella_domestic_goddess_recipes(soup: BeautifulSoup, epub_path: str) -> List[Dict]:
    """Extract recipes from Nigella Lawson's 'How to be a Domestic Goddess'.

    Recipes are in individual small HTML files with the title in
    <h3 class="h3a">, optional intro paragraphs, ingredients in a
    <div class="tbspace"> with paragraphs, and method paragraphs outside it.
    """
    recipes = []
    for title_tag in soup.find_all('h3', class_='h3a'):
        title = _normalize_whitespace(title_tag.get_text(' ', strip=True))
        if not title or len(title) < 4 or len(title) > 120:
            continue

        tbspace = title_tag.find_next_sibling('div', class_='tbspace')
        if not tbspace:
            continue

        ingredients = []
        for p in tbspace.find_all('p'):
            line = _normalize_whitespace(p.get_text(' ', strip=True))
            if line:
                if line.lower().startswith('for the') or line.endswith(':'):
                    ingredients.append('--- ' + line)
                else:
                    ingredients.append(line)

        steps = []
        serves = ''
        for sib in tbspace.find_next_siblings():
            if sib.name in ('h3', 'h2', 'h1'):
                break
            if sib.name != 'p':
                continue
            text = _normalize_whitespace(sib.get_text(' ', strip=True))
            if not text:
                continue
            if _is_serves_line(text):
                serves += ' ' + text
            else:
                steps.append(text)

        if len(ingredients) < 2 or len(steps) < 1:
            continue

        recipes.append({
            'title': title,
            'ingredients': '\n'.join(ingredients).strip(),
            'steps': '\n'.join(steps).strip(),
            'source': os.path.basename(epub_path),
            'file_path': epub_path,
            'image': '',
            'serves': serves.strip(),
        })

    return recipes
