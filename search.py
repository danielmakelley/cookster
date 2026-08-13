import argparse
import sqlite3


def search_db(db_path: str, query: str, limit: int = 10):
    from ranking import rank_recipes

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    candidates = []
    try:
        c.execute("SELECT rowid FROM recipes_fts WHERE recipes_fts MATCH ?", (query,))
        ids = [r[0] for r in c.fetchall()]
        if ids:
            placeholder = ','.join('?' for _ in ids)
            c.execute(f"SELECT id, title, ingredients, steps, source FROM recipes WHERE id IN ({placeholder})", ids)
            rows = c.fetchall()
        else:
            rows = []
    except sqlite3.OperationalError:
        c.execute("SELECT id, title, ingredients, steps, source FROM recipes")
        rows = c.fetchall()
    conn.close()
    for r in rows:
        candidates.append({'id': r[0], 'title': r[1], 'ingredients': r[2] or '', 'steps': r[3] or '', 'source': r[4]})
    ranked = rank_recipes(candidates, query, top_n=limit)
    return ranked


def main():
    p = argparse.ArgumentParser(description='Search recipes in cookster DB')
    p.add_argument('--db', default='cookster.db')
    p.add_argument('--query', required=True)
    p.add_argument('--limit', type=int, default=10)
    args = p.parse_args()
    rows = search_db(args.db, args.query, args.limit)
    if not rows:
        print('No results')
        return
    for r in rows:
        print('---')
        print(f'Title: {r["title"]}')
        print(f'Source: {r["source"]}')
        if r.get('ingredients'):
            print('\nIngredients:\n' + r['ingredients'][:1000])
        if r.get('steps'):
            print('\nSteps:\n' + r['steps'][:1000])


if __name__ == '__main__':
    main()
