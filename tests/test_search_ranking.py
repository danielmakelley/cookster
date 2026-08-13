import sqlite3
import tempfile
import os
from indexer import create_db
from search import search_db


def make_db_with_samples(path):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('CREATE TABLE recipes (id INTEGER PRIMARY KEY, title TEXT, ingredients TEXT, steps TEXT, source TEXT, file_path TEXT)')
    samples = [
        ('Grilled Chicken','chicken, salt, pepper','grill the chicken','book1','/a.epub'),
        ('Apple Pie','apples, sugar, flour','bake the pie','book2','/b.epub'),
        ('Chicken Soup','chicken, water, carrots','boil the chicken','book3','/c.epub'),
    ]
    for t, ing, steps, src, fp in samples:
        c.execute('INSERT INTO recipes (title, ingredients, steps, source, file_path) VALUES (?,?,?,?,?)',(t,ing,steps,src,fp))
    conn.commit()
    conn.close()


def test_chicken_ranks_top():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    make_db_with_samples(path)
    results = search_db(path, 'chicken', limit=2)
    # results are dicts; top should mention chicken in title or ingredients
    assert len(results) >= 1
    top = results[0]
    assert 'chicken' in (top['title'].lower() + top['ingredients'].lower())
    os.remove(path)
