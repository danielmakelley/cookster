from indexer import _is_pdf_title, _is_non_cookbook_source, _is_serves_line


def test_pdf_title_heuristics():
    assert _is_pdf_title('Blackened Seasoning') is True
    assert _is_pdf_title('BLACKENED SEASONING') is True
    # Single-word all-caps titles are valid for short cookbook titles (e.g. "BERBERE")
    assert _is_pdf_title('BERBERE') is True
    # Subtitles / ingredient lists are not titles
    assert _is_pdf_title('Paprika, Cumin, Coriander, Black Pepper, White Pepper') is False
    # Section headings, copyright, and prose are not titles
    assert _is_pdf_title('Includes bibliographical references and index.') is False
    assert _is_pdf_title('Contents') is False
    assert _is_pdf_title('Yield') is False


def test_non_cookbook_source_blacklist():
    assert _is_non_cookbook_source('Becoming_Vegan_The_Complete_Reference_to_Plant-Based_Nutrition.pdf') is True
    assert _is_non_cookbook_source('The Blue Zones_ 9 Lessons for Living Longer.pdf') is True
    assert _is_non_cookbook_source('Forks-over-knives-family-every-parent-s-guide-to-raising-healthy-happy-kids.pdf') is True
    assert _is_non_cookbook_source('Afro-Vegan.pdf') is False


def test_unique_books_prefers_larger_duplicate(tmp_path):
    from indexer import _unique_books
    (tmp_path / 'a.epub').write_text('small')
    (tmp_path / 'a (1).epub').write_text('this is a larger duplicate file')
    (tmp_path / 'b.pdf').write_text('pdf content')
    result = _unique_books(str(tmp_path))
    assert len(result) == 2
    assert str(tmp_path / 'a (1).epub') in result
    assert str(tmp_path / 'b.pdf') in result


def test_serves_line_detection():
    assert _is_serves_line('Serves 4') is True
    assert _is_serves_line('YIELD 2 cups') is True  # yield keyword + quantity
    assert _is_serves_line('Blackened Seasoning') is False
