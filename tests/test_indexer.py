import sys
import pytest
from bs4 import BeautifulSoup
import ebooklib

sys.path.insert(0, '.')

from indexer import (
    _extract_schema_org_recipes,
    _extract_from_soup,
    _find_image_for_doc,
    _cleanup_orphan_image_dirs,
    _extract_one_pan_wonders_recipes,
    _extract_gordon_ramsay_recipes,
    _extract_simply_japanese_recipes,
    _extract_plenty_more_recipes,
    _extract_flavour_recipes,
    _extract_plenty_recipes,
    _extract_veganomicon_recipes,
    _extract_french_provincial_recipes,
    _extract_delias_cakes_recipes,
    _extract_good_things_recipes,
    _extract_everyday_super_food_recipes,
    _extract_jamie_veg_recipes,
    _extract_seven_fires_recipes,
    _extract_cocolat_recipes,
    _extract_kitchen_diaries_recipes,
    _extract_nigella_how_to_eat_recipes,
    _extract_nigella_domestic_goddess_recipes,
    _is_ingredient_line,
)


class MockEpubItem:
    def __init__(self, name, html, item_type=ebooklib.ITEM_DOCUMENT):
        self._name = name
        self._type = item_type
        self._html = html

    def get_type(self):
        return self._type

    def get_content(self):
        return self._html.encode('utf-8')

    def get_name(self):
        return self._name


def test_schema_org_extracts_multiple_recipes():
    html = """<html><body>
        <div itemscope itemtype="http://schema.org/Recipe">
            <h1 itemprop="name">Soup A</h1>
            <span itemprop="recipeIngredient">1 onion</span>
            <span itemprop="recipeIngredient">2 cups stock</span>
            <div itemprop="recipeInstructions"><p>Chop onion.</p><p>Simmer.</p></div>
        </div>
        <div itemscope itemtype="https://schema.org/Recipe">
            <h1 itemprop="name">Soup B</h1>
            <span itemprop="recipeIngredient">2 carrots</span>
            <span itemprop="recipeIngredient">1 litre water</span>
            <ul itemprop="recipeInstructions"><li>Grate carrots.</li><li>Boil.</li></ul>
        </div>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_schema_org_recipes(soup, 'book.epub', image_path='img.jpg')
    assert len(recs) == 2
    titles = [r['title'] for r in recs]
    assert 'Soup A' in titles
    assert 'Soup B' in titles
    for r in recs:
        assert r['image'] == 'img.jpg'
        assert r['ingredients']
        assert r['steps']


def test_extract_from_soup_uses_registry_for_schema_org():
    html = """<div itemscope itemtype="http://schema.org/Recipe">
        <h1 itemprop="name">Cake</h1>
        <span itemprop="recipeIngredient">1 cup flour</span>
        <span itemprop="recipeIngredient">2 eggs</span>
        <div itemprop="recipeInstructions"><p>Mix.</p><p>Bake.</p></div>
    </div>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_from_soup(soup, 'book.epub', image_path='pic.jpg')
    assert len(recs) == 1
    assert recs[0]['title'] == 'Cake'
    assert recs[0]['image'] == 'pic.jpg'
    assert '1 cup flour' in recs[0]['ingredients']


def test_find_image_for_doc_checks_current_document():
    html = '<html><img src="dish.jpg"/><p>Recipe</p></html>'
    items = [MockEpubItem('recipe.xhtml', html)]
    saved_images = {'dish.jpg': 'static/epub_images/book_hash/dish.jpg'}
    images_dir = 'static/epub_images/book_hash'
    soup = BeautifulSoup(html, 'lxml')
    result = _find_image_for_doc(items, 0, soup, items[0].get_name(), saved_images, images_dir)
    assert result == 'static/epub_images/book_hash/dish.jpg'


def test_find_image_for_doc_checks_preceding_neighbor():
    items = [
        MockEpubItem('cover.xhtml', '<html><img src="cover.jpg"/></html>'),
        MockEpubItem('recipe.xhtml', '<html><p>Recipe text</p></html>'),
    ]
    saved_images = {'cover.jpg': 'static/epub_images/book_hash/cover.jpg'}
    images_dir = 'static/epub_images/book_hash'
    soup = BeautifulSoup('<html><p>Recipe text</p></html>', 'lxml')
    result = _find_image_for_doc(items, 1, soup, items[1].get_name(), saved_images, images_dir)
    assert result == 'static/epub_images/book_hash/cover.jpg'


def test_find_image_for_doc_checks_following_neighbor():
    items = [
        MockEpubItem('recipe.xhtml', '<html><p>Recipe text</p></html>'),
        MockEpubItem('img.xhtml', '<html><img src="dish.jpg"/></html>'),
    ]
    saved_images = {'dish.jpg': 'static/epub_images/book_hash/dish.jpg'}
    images_dir = 'static/epub_images/book_hash'
    soup = BeautifulSoup('<html><p>Recipe text</p></html>', 'lxml')
    result = _find_image_for_doc(items, 0, soup, items[0].get_name(), saved_images, images_dir)
    assert result == 'static/epub_images/book_hash/dish.jpg'


def test_find_image_for_doc_ignores_text_heavy_neighbors():
    items = [
        MockEpubItem('recipe.xhtml', '<html><p>Recipe text</p></html>'),
        MockEpubItem('intro.xhtml', '<html><p>' + ('Lots of text. ' * 50) + '<img src="dish.jpg"/></p></html>'),
    ]
    saved_images = {'dish.jpg': 'static/epub_images/book_hash/dish.jpg'}
    images_dir = 'static/epub_images/book_hash'
    soup = BeautifulSoup('<html><p>Recipe text</p></html>', 'lxml')
    result = _find_image_for_doc(items, 0, soup, items[0].get_name(), saved_images, images_dir)
    assert result == ''


def test_cleanup_orphan_image_dirs_removes_stale_dirs(tmp_path):
    base = tmp_path / 'epub_images'
    base.mkdir()
    (base / 'expected_hash').mkdir()
    (base / 'orphan_hash').mkdir()
    (base / 'orphan_hash' / 'file.jpg').write_text('x')
    _cleanup_orphan_image_dirs(str(base), {'expected_hash'})
    assert (base / 'expected_hash').exists()
    assert not (base / 'orphan_hash').exists()


def test_registry_extractors_accept_three_args():
    """Every registered extractor must accept (soup, epub_path, image_path)."""
    from indexer import _EXTRACTORS
    dummy_soup = BeautifulSoup('<html><p>dummy</p></html>', 'lxml')
    for entry in _EXTRACTORS:
        try:
            entry['extract'](dummy_soup, 'book.epub', 'img.jpg')
        except TypeError as e:
            if 'positional argument' in str(e):
                pytest.fail(f"Extractor {entry['name']!r} does not accept (soup, epub_path, image_path): {e}")


def test_one_pan_wonders_extracts_blockquote_ingredients():
    html = """<html><body>
        <p class="calibre_12"><span class="calibre2"><span class="calibre_4">SMOKED SALMON PASTA</span></span></p>
        <p class="calibre_12">SPINACH, SPRING ONION, LEMON, CURDS &amp; PARMESAN</p>
        <p class="calibre_12">SERVES 1 | TOTAL 8 MINUTES</p>
        <blockquote class="calibre_24"><span class="calibre_1">125g fresh lasagne sheets</span></blockquote>
        <blockquote class="calibre_24"><span class="calibre_1">2 spring onions</span></blockquote>
        <p class="calibre_5"><span class="calibre_1">Boil the kettle. Cook the pasta.</span></p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_one_pan_wonders_recipes(soup, 'onepan.epub')
    assert len(recs) == 1
    assert 'SMOKED SALMON PASTA' in recs[0]['title']
    assert '125g fresh lasagne sheets' in recs[0]['ingredients']
    assert '2 spring onions' in recs[0]['ingredients']
    assert 'Boil the kettle' in recs[0]['steps']


def test_gordon_ramsay_extracts_from_classes():
    html = """<html><body>
        <p class="recipe-head">SEA BASS WITH FENNEL,<br/>LEMON AND CAPERS</p>
        <p class="serving">SERVES 4</p>
        <p class="fm">Cooking fish in individual foil packets...</p>
        <div class="hang">
            <p class="ingredients">2 sea bass, 1.25kg</p>
            <p class="ingredients">2 small fennel bulbs</p>
        </div>
        <p class="method1"><strong>1</strong>. Preheat the oven.</p>
        <p class="method1"><strong>2</strong>. Season the fish.</p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_gordon_ramsay_recipes(soup, 'ramsay.epub')
    assert len(recs) == 1
    assert 'SEA BASS WITH FENNEL' in recs[0]['title']
    assert '2 sea bass' in recs[0]['ingredients']
    assert 'Preheat the oven' in recs[0]['steps']


def test_simply_japanese_extracts_sub_recipes():
    html = """<html><body>
        <p class="rct">Various Miso Soups</p>
        <p class="ingtc">RED MISO</p>
        <p class="ing">Serves 4</p>
        <p class="pret">Clams</p>
        <p class="ing">200 g clams</p>
        <p class="text1">Remove the sand from the clams.</p>
        <p class="textt">Natto</p>
        <p class="ing">4 tablespoons natto</p>
        <p class="text1">Bring the dashi to a boil.</p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_simply_japanese_recipes(soup, 'japanese.epub')
    assert len(recs) == 2
    titles = [r['title'] for r in recs]
    assert 'Various Miso Soups - RED MISO' in titles
    assert 'Various Miso Soups - Natto' in titles
    red = next(r for r in recs if 'RED MISO' in r['title'])
    assert '200 g clams' in red['ingredients']
    assert 'Remove the sand' in red['steps']


def test_ingredient_line_rejects_packets_substring():
    """A sentence containing 'packets' should not be treated as an ingredient."""
    text = 'Cooking fish in individual foil packets, or en papillote...'
    assert not _is_ingredient_line(text)


def test_plenty_more_extracts_div_recipe():
    html = """<html><body>
        <div class="recipe">
            <h1 class="recipe_title">TOMATO AND POMEGRANATE SALAD</h1>
            <div class="yield">SERVES FOUR</div>
            <div class="headnote"><p>A fresh salad.</p></div>
            <div class="ingredients">
                <div class="IL_item">2 large tomatoes, cut into wedges</div>
                <div class="IL_item">1 pomegranate, seeds removed</div>
                <div class="IL_item">2 tbsp olive oil</div>
            </div>
            <div class="method_step">Mix the tomatoes and pomegranate seeds.</div>
            <div class="method_step">Drizzle with olive oil and serve.</div>
        </div>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_plenty_more_recipes(soup, 'plenty_more.epub')
    assert len(recs) == 1
    assert recs[0]['title'] == 'TOMATO AND POMEGRANATE SALAD'
    assert 'SERVES FOUR' in recs[0]['serves']
    assert '2 large tomatoes' in recs[0]['ingredients']
    assert 'Mix the tomatoes' in recs[0]['steps']


def test_flavour_extracts_bold_title_and_numbered_steps():
    html = """<html><body>
        <p class="calibre_13"><span class="bold">CALVIN’S GRILLED PEACHES</span></p>
        <p class="calibre_12">A lovely summer dish.</p>
        <p class="calibre_40"><span class="bold">SERVES FOUR</span></p>
        <ul class="calibre_41">
            <li class="calibre_42">400g runner beans</li>
            <li class="calibre_42">3 tbsp olive oil</li>
        </ul>
        <p class="calibre_13"><span class="bold">1.</span> Toss the beans with oil.</p>
        <p class="calibre_13"><span class="bold">2.</span> Grill for 5 minutes.</p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_flavour_recipes(soup, 'flavour.epub')
    assert len(recs) == 1
    assert 'CALVIN’' in recs[0]['title']
    assert '400g runner beans' in recs[0]['ingredients']
    assert 'Toss the beans' in recs[0]['steps']


def test_plenty_2011_extracts_italian_recipe():
    html = """<html><body>
        <h2 class="section2"><strong class="calibre4">Verdure baby in camicia</strong></h2>
        <p class="nonindent">A light way with vegetables.</p>
        <div class="recipe">
            <p class="recipe1">Per quattro</p>
            <p class="recipe1">200 g di carote</p>
            <p class="recipe1">100 g di finocchi</p>
            <p class="recipe2">Maionese</p>
            <p class="recipe1">1 tuorlo d’uovo</p>
        </div>
        <p class="nonindent">Cominciate con la maionese.</p>
        <p class="nonindent1">Lavate le verdure.</p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_plenty_recipes(soup, 'plenty.epub')
    assert len(recs) == 1
    assert recs[0]['title'] == 'Verdure baby in camicia'
    assert 'Per quattro' in recs[0]['serves']
    assert '200 g di carote' in recs[0]['ingredients']
    assert '--- Maionese' in recs[0]['ingredients']
    assert 'Cominciate con la maionese' in recs[0]['steps']


def test_veganomicon_extracts_chapter_title_pair():
    html = """<html><body>
        <h1 class="chapter-title"><span class="koboSpan">SPICY TEMPEH</span></h1>
        <h2 class="chapter-subtitle"><span class="koboSpan">NORI ROLLS</span></h2>
        <div class="recipe">
            <p class="yield">MAKES 4 ROLLS</p>
            <div class="headnote"><p>Great party food.</p></div>
            <div class="ingredients">
                <p class="ingredient">1 cup sushi rice</p>
                <p class="ingredient">4 sheets nori</p>
            </div>
            <div class="procedure">
                <p class="step"><span class="blue">Prepare the rice:</span> Cook the rice.</p>
                <p class="step-nl"><span class="blue">1.</span> Roll the nori.</p>
            </div>
        </div>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_veganomicon_recipes(soup, 'veganomicon.epub')
    assert len(recs) == 1
    assert 'SPICY TEMPEH' in recs[0]['title']
    assert 'NORI ROLLS' in recs[0]['title']
    assert '1 cup sushi rice' in recs[0]['ingredients']
    assert 'Roll the nori' in recs[0]['steps']


def test_french_provincial_extracts_h1_h2_title():
    html = """<html><body>
        <h1 class="h1"><b>SAUCE BERCY</b></h1>
        <h2 class="h1"><b>WHITE WINE AND SHALLOT SAUCE</b></h2>
        <div class="tx1">A useful hot sauce.</div>
        <div class="tx">Chop 4 shallots very finely. Put them in a saucepan with half a glass of dry white wine.</div>
        <div class="tx">Add 2 tablespoons of the gravy and 1 oz. of good butter.</div>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_french_provincial_recipes(soup, 'french.epub')
    assert len(recs) == 1
    assert 'SAUCE BERCY' in recs[0]['title']
    assert 'WHITE WINE AND SHALLOT SAUCE' in recs[0]['title']
    assert '4 shallots' in recs[0]['ingredients']
    assert '2 tablespoons' in recs[0]['ingredients']


def test_french_provincial_skips_section_heading():
    html = """<html><body>
        <h1 class="h1"><b>WINE FOR THE KITCHEN</b></h1>
        <div class="tx1">A few words about choosing wine.</div>
        <div class="tx">A good Burgundy is always welcome.</div>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_french_provincial_recipes(soup, 'french.epub')
    assert len(recs) == 0


def test_book_specific_extractor_blocks_generic_extractors():
    """A book with a dedicated extractor should not fall through to generic extractors."""
    html = """<html><body>
        <h1 class="h1"><b>Gastronomie Pratique</b></h1>
        <h2>INGREDIENTS</h2>
        <ul><li>1 cup flour</li><li>2 oz sugar</li></ul>
        <h2>METHOD</h2>
        <p>Mix and bake.</p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    # The generic heading extractor would claim this as a recipe; the dedicated
    # French Provincial extractor should match first and return nothing.
    recs = _extract_from_soup(soup, 'French Provincial Cooking.epub')
    assert len(recs) == 0


def test_delias_cakes_extracts_ingredients_and_steps():
    html = """<html><body>
        <p class="recipe-head">CLASSIC SPONGE CAKE</p>
        <p class="text-intro">A classic sponge.</p>
        <p class="recipe-text-top">115g self-raising flour</p>
        <p class="recipe-text">2 large eggs</p>
        <p class="recipe-text">1 teaspoon vanilla extract</p>
        <p class="recipe-text-bottom">Preheat the oven to 170°C.</p>
        <p class="text-center">Sift the flour and baking powder into a bowl.</p>
        <p class="text-center">Bake for 25 minutes.</p>
        <p class="recipe-head">NEXT RECIPE</p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_delias_cakes_recipes(soup, 'delias.epub')
    assert len(recs) == 1
    assert recs[0]['title'] == 'CLASSIC SPONGE CAKE'
    assert '115g self-raising flour' in recs[0]['ingredients']
    assert 'Bake for 25 minutes.' in recs[0]['steps']
    assert 'text-intro' not in recs[0]['ingredients']


def test_good_things_extracts_embedded_recipe():
    html = """<html><body>
        <h1>Trout</h1>
        <h2>Truite à la meunière</h2>
        <p>4 trout, about 8 oz each</p>
        <p>3 oz butter</p>
        <p>First clarify the butter by bringing it to the boil.</p>
        <p>Rinse the trout quickly, wipe them dry and dip each one in milk.</p>
        <h2>Baked trout</h2>
        <p>4 trout, about 8 oz each</p>
        <p>4 oz breadcrumbs</p>
        <p>Melt the onion gently in butter.</p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_good_things_recipes(soup, 'good_things.epub')
    assert len(recs) >= 1
    titles = [r['title'] for r in recs]
    assert 'Truite à la meunière' in titles


def test_everyday_super_food_extracts_sidebar_recipe():
    html = """<html><body>
        <h2>BAKED EGGS<br/>WITH BEANS</h2>
        <div class="jamie_super_food_recipe_intro"><span>Healthy and tasty.</span></div>
        <aside class="sidebar_wrapper">
            <h5>SERVES 2<br/>20 MINUTES</h5>
            <p>250g cherry tomatoes</p>
            <p>2 large eggs</p>
        </aside>
        <div class="maincontent_wrapper">
            <p>Halve the tomatoes.</p>
            <p>Crack in the eggs.</p>
        </div>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_everyday_super_food_recipes(soup, 'everyday.epub')
    assert len(recs) == 1
    assert 'BAKED EGGS' in recs[0]['title']
    assert '250g cherry tomatoes' in recs[0]['ingredients']
    assert 'Crack in the eggs.' in recs[0]['steps']


def test_jamie_veg_extracts_recipe_section():
    html = """<html><body>
        <section class="calibre1">
            <h2 class="rec_head1">SIMPLE PICKLE</h2>
            <h2 class="rec_subhead">SEASONAL VEG</h2>
            <h5 class="serves">MAKES 1 JAR</h5>
            <section class="sidebar_wrapper">
                <ul class="ingredient_items">
                    <li>500ml cider vinegar</li>
                    <li>500g vegetables</li>
                </ul>
            </section>
            <section class="maincontent_wrapper">
                <p>Tip the vinegar into a pan.</p>
                <p>Add the vegetables.</p>
            </section>
        </section>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_jamie_veg_recipes(soup, 'jamie_veg.epub')
    assert len(recs) == 1
    assert recs[0]['title'] == 'SIMPLE PICKLE – SEASONAL VEG'
    assert '500ml cider vinegar' in recs[0]['ingredients']
    assert 'Tip the vinegar into a pan.' in recs[0]['steps']


def test_seven_fires_extracts_rh_recipe():
    html = """<html><body>
        <p class="RH">Zucchini with Basil, Mint, and Parmesan</p>
        <p class="RHN">Very fresh tasting. | Serves 4</p>
        <p class="RI-M"><strong>1 good-sized zucchini</strong></p>
        <p class="RI-M"><strong>1 lemon</strong></p>
        <p class="RI-L"><strong>Sliced baguette</strong></p>
        <p class="TX">With a sharp knife, slice the zucchini.</p>
        <p class="TX1">Grate the zest of half the lemon over the zucchini.</p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_seven_fires_recipes(soup, 'seven_fires.epub')
    assert len(recs) == 1
    assert recs[0]['title'] == 'Zucchini with Basil, Mint, and Parmesan'
    assert '1 good-sized zucchini' in recs[0]['ingredients']
    assert 'With a sharp knife, slice the zucchini.' in recs[0]['steps']


def test_cocolat_extracts_numbered_steps():
    html = """<html><body>
        <h1 class="h1">Gâteau Grand Marnier</h1>
        <p class="bkauthor">Serves 10–12</p>
        <p class="extract-center">Ingredients:</p>
        <p class="extract-indent">⅓ cup Grand Marnier</p>
        <p class="extract-indent">8-inch Chocolate Génoise</p>
        <p class="extract-center">Special Equipment:</p>
        <p class="extract-indent">8-inch cake circle</p>
        <p class="bodytext">1. Combine Grand Marnier with Simple Syrup.</p>
        <p class="bodytext">2. Use a serrated knife to cut the Génoise.</p>
        <h1 class="h1">Next Cake</h1>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_cocolat_recipes(soup, 'cocolat.epub')
    assert len(recs) == 1
    assert recs[0]['title'] == 'Gâteau Grand Marnier'
    assert '⅓ cup Grand Marnier' in recs[0]['ingredients']
    assert '--- Special Equipment:' in recs[0]['ingredients']
    assert '1. Combine Grand Marnier' in recs[0]['steps']


def test_kitchen_diaries_extracts_diary_recipe():
    html = """<html><body>
        <h2 class="subhead1">August 1 A summer day</h2>
        <h2 class="subhead2">Bream with lemon and anchovy potatoes</h2>
        <div class="recp">
            <p class="recp_txt">sea bream – 4 whole fish</p>
            <p class="recp_txt">olive oil</p>
            <p class="recp_txt">For the potatoes: waxy potatoes – 1kg</p>
        </div>
        <p class="none">Set the oven at 200°C/Gas 6.</p>
        <p class="normal">Lay the fish in a roasting tin.</p>
        <p class="none">Enough for 4</p>
        <h2 class="subhead1">August 2</h2>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_kitchen_diaries_recipes(soup, 'kitchen_diaries.epub')
    assert len(recs) == 1
    assert recs[0]['title'] == 'Bream with lemon and anchovy potatoes'
    assert 'sea bream – 4 whole fish' in recs[0]['ingredients']
    assert 'Set the oven at 200°C/Gas 6.' in recs[0]['steps']


def test_nigella_how_to_eat_extracts_recipe():
    html = """<html><body>
        <h2 class="recipes-head">LINGUINE WITH CLAMS</h2>
        <p class="recipes-para">200g clams</p>
        <p class="recipes-para1">150g linguine</p>
        <p class="recipes-paraa">1 clove garlic</p>
        <p class="flush-lefts">Put the clams to soak in cold water.</p>
        <p class="indenteds">Mince the garlic and cook gently.</p>
        <p class="indenteds-space-after">Serves 1.</p>
        <h2 class="recipes-head">COD WITH CLAMS</h2>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_nigella_how_to_eat_recipes(soup, 'how_to_eat.epub')
    assert len(recs) == 1
    assert recs[0]['title'] == 'LINGUINE WITH CLAMS'
    assert '200g clams' in recs[0]['ingredients']
    assert 'Put the clams to soak in cold water.' in recs[0]['steps']


def test_nigella_domestic_goddess_extracts_cake():
    html = """<html><body>
        <h3 class="h3a">GATEAU BRETON</h3>
        <p class="normal2">A delicious cake.</p>
        <div class="tbspace">
            <p class="normalf2">for the cake:</p>
            <p class="normalf">225g plain flour</p>
            <p class="normalf">250g caster sugar</p>
            <p class="normalf1">for the glaze:</p>
            <p class="normalf">1 teaspoon of egg yolk</p>
        </div>
        <p class="normal">Preheat the oven to 190°C.</p>
        <p class="bodytext">Put the flour into a bowl.</p>
        <p class="bodytext">Serves 8–10.</p>
    </body></html>"""
    soup = BeautifulSoup(html, 'lxml')
    recs = _extract_nigella_domestic_goddess_recipes(soup, 'domestic_goddess.epub')
    assert len(recs) == 1
    assert recs[0]['title'] == 'GATEAU BRETON'
    assert '225g plain flour' in recs[0]['ingredients']
    assert '--- for the glaze:' in recs[0]['ingredients']
    assert 'Preheat the oven to 190°C.' in recs[0]['steps']


import json
import os
import sqlite3
import tempfile

from indexer import index_preprocessed_dir


def test_incremental_index_skips_unchanged_books():
    with tempfile.TemporaryDirectory() as recipes_dir, tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, 'test.db')

        # First book
        book1 = os.path.join(recipes_dir, 'book1.json')
        with open(book1, 'w', encoding='utf-8') as f:
            json.dump([{
                'title': 'Soup',
                'ingredients': 'water\nsalt',
                'steps': 'boil',
                'source': 'book1.epub',
                'file_path': 'book1.epub',
                'image': '',
                'serves': '',
            }], f)

        index_preprocessed_dir(recipes_dir, db_path)
        conn = sqlite3.connect(db_path)
        count1 = conn.execute('SELECT COUNT(*) FROM recipes').fetchone()[0]
        log1 = conn.execute('SELECT json_mtime FROM book_index_log WHERE source = ?', ('book1.epub',)).fetchone()
        conn.close()
        assert count1 == 1
        assert log1 is not None

        # Re-run without changes; no new inserts should happen.
        index_preprocessed_dir(recipes_dir, db_path)
        conn = sqlite3.connect(db_path)
        count2 = conn.execute('SELECT COUNT(*) FROM recipes').fetchone()[0]
        conn.close()
        assert count2 == 1

        # Modify the book and re-index; count stays 1 but log updates.
        with open(book1, 'w', encoding='utf-8') as f:
            json.dump([{
                'title': 'Better Soup',
                'ingredients': 'water\nsalt\npepper',
                'steps': 'boil\nserve',
                'source': 'book1.epub',
                'file_path': 'book1.epub',
                'image': '',
                'serves': '',
            }], f)
        index_preprocessed_dir(recipes_dir, db_path)
        conn = sqlite3.connect(db_path)
        titles = [r[0] for r in conn.execute('SELECT title FROM recipes')]
        log2 = conn.execute('SELECT json_mtime FROM book_index_log WHERE source = ?', ('book1.epub',)).fetchone()
        conn.close()
        assert titles == ['Better Soup']
        assert log2[0] > log1[0]


def test_incremental_index_removes_deleted_books():
    with tempfile.TemporaryDirectory() as recipes_dir, tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, 'test.db')

        for slug, source in [('book_a', 'book_a.epub'), ('book_b', 'book_b.epub')]:
            path = os.path.join(recipes_dir, f'{slug}.json')
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([{
                    'title': f'{slug} recipe',
                    'ingredients': 'x',
                    'steps': 'y',
                    'source': source,
                    'file_path': source,
                    'image': '',
                    'serves': '',
                }], f)

        index_preprocessed_dir(recipes_dir, db_path)
        conn = sqlite3.connect(db_path)
        assert conn.execute('SELECT COUNT(*) FROM recipes').fetchone()[0] == 2
        conn.close()

        os.remove(os.path.join(recipes_dir, 'book_b.json'))
        index_preprocessed_dir(recipes_dir, db_path)
        conn = sqlite3.connect(db_path)
        sources = [r[0] for r in conn.execute('SELECT source FROM recipes')]
        logs = [r[0] for r in conn.execute('SELECT source FROM book_index_log')]
        conn.close()
        assert sources == ['book_a.epub']
        assert logs == ['book_a.epub']
