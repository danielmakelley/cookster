import argparse
from indexer import build_index


def main():
    p = argparse.ArgumentParser(description='Preprocess cookbooks and index into a sqlite DB')
    p.add_argument('--books-dir', '--epub-dir', dest='books_dir', default='books',
                   help='Directory containing .epub and .pdf files')
    p.add_argument('--recipes-dir', default='data/recipes',
                   help='Directory to write preprocessed JSON recipes')
    p.add_argument('--db', default='cookster.db', help='SQLite DB path')
    p.add_argument('--force', action='store_true',
                   help='Re-parse all books even if their JSON is up to date')
    args = p.parse_args()
    build_index(args.books_dir, args.recipes_dir, args.db, force=args.force)


if __name__ == '__main__':
    main()
