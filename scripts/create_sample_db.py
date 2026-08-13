import sqlite3
import os
import sys
# ensure project root is on sys.path so imports work when running from scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from indexer import create_db


DB = os.path.join(os.path.dirname(__file__), '..', 'cookster.db')


def main():
    create_db(DB)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    samples = [
        {'title': 'Roasted Eggplant', 'ingredients': 'eggplant, olive oil, salt', 'steps': 'Cut eggplant and roast at 200C for 30 minutes.', 'source': 'sample', 'file_path': ''},
        {'title': 'Classic Chicken Soup', 'ingredients': 'chicken, carrots, celery, water, salt', 'steps': 'Simmer chicken with vegetables for 2 hours.', 'source': 'sample', 'file_path': ''}
    ]
    for r in samples:
        c.execute('INSERT INTO recipes (title, ingredients, steps, source, file_path) VALUES (?,?,?,?,?)', (r['title'], r['ingredients'], r['steps'], r['source'], r['file_path']))
        rowid = c.lastrowid
        try:
            c.execute('INSERT INTO recipes_fts(rowid, title, ingredients, steps) VALUES (?,?,?,?)', (rowid, r['title'], r['ingredients'], r['steps']))
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()
    print('Created sample DB at', os.path.abspath(DB))


if __name__ == '__main__':
    main()
