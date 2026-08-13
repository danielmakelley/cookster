"""Watch the books/ directory and re-index when files change.

This is a lightweight polling watcher. It calls the same incremental indexer
used by run_index.py, so unchanged books are skipped quickly.
"""
import argparse
import os
import sys
import time

from indexer import build_index


def main():
    parser = argparse.ArgumentParser(description='Watch books/ and rebuild the Cookster index when files change.')
    parser.add_argument('--books-dir', default='books', help='Directory containing EPUB/PDF files')
    parser.add_argument('--recipes-dir', default='data/recipes', help='Directory for preprocessed JSON')
    parser.add_argument('--db', default='cookster.db', help='SQLite database path')
    parser.add_argument('--interval', type=int, default=10, help='Polling interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run one indexing pass and exit')
    args = parser.parse_args()

    books_dir = os.path.abspath(args.books_dir)
    recipes_dir = os.path.abspath(args.recipes_dir)
    db_path = os.path.abspath(args.db)

    if not os.path.isdir(books_dir):
        print(f'Books directory not found: {books_dir}', file=sys.stderr)
        sys.exit(1)

    print(f'Watching {books_dir} (interval={args.interval}s, db={db_path})')

    try:
        while True:
            try:
                build_index(books_dir, recipes_dir, db_path, force=False)
            except Exception as e:
                print(f'Indexing error: {e}', file=sys.stderr)
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('\nWatcher stopped.')


if __name__ == '__main__':
    main()
