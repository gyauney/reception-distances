import json
import csv
from collections import defaultdict
import pandas as pd
import itertools
import argparse
import operator
import gzip
import os

def goodreads_read_events(fn):
    print('Reading all Goodreads events:')
    df = pd.read_csv('data/book_id_map.csv', dtype = str)
    csv_id_to_goodreads_book_id = df.set_index('book_id_csv')['book_id'].to_dict()

    user_to_books = defaultdict(set)
    book_to_users = defaultdict(set)
    with open(fn, 'r') as f:
        csvreader = csv.reader(f)
        for i, row in enumerate(csvreader):
            if i == 0:
                continue
            if i % 1000000 == 0:
                print('    reading row {}'.format(i))
            csv_book_id = row[1]
            reviewed = row[4]
            if reviewed != '1':
               continue
            goodreads_book_id = csv_id_to_goodreads_book_id[csv_book_id]
            csv_user_id = row[0]
            user_to_books[csv_user_id].add(goodreads_book_id)
            book_to_users[goodreads_book_id].add(csv_user_id)
    print('Done reading events!!!')

    print('Number of unique users: {}'.format(len(user_to_books)))
    print('Number of unique books: {}'.format(len(book_to_users)))

    return user_to_books, book_to_users

# read in cached user-book interactions if they exist
def get_cached_goodreads_events():
    user_to_books_fn = 'data/cached_user-to-books.json'
    book_to_users_fn = 'data/cached_book-to-users.json'
    if os.path.exists(user_to_books_fn) and os.path.exists(book_to_users_fn):
        print('Reading user_to_books!')
        with open(user_to_books_fn, 'r') as f:
            user_to_books = json.load(f)
        print('Reading book_to_users!')
        with open(book_to_users_fn, 'r') as f:
            book_to_users = json.load(f)
        return user_to_books, book_to_users
    user_to_books, book_to_users = goodreads_read_events('data/goodreads_interactions.csv')
    print('Saving user_to_books!')
    with open(user_to_books_fn, 'w') as f:
        json.dump({u: list(b) for u, b in user_to_books.items()}, f)
    print('Saving book_to_users!')
    with open(book_to_users_fn, 'w') as f:
        json.dump({b: list(u) for b, u in book_to_users.items()}, f)
    return user_to_books, book_to_users

def get_books_to_degrees(user_to_books, book_to_users):
    degree_fn = 'data/cached_book-id-to-degree.json'
    ranked_fn = 'data/cached_book-id-to-degree-rank.json'
    sorted_fn = 'data/cached_book-ids-with-degrees-sorted.json'
    if os.path.exists(degree_fn):
        print('Reading degrees.')
        with open(degree_fn, 'r') as f:
            book_id_to_degree = json.load(f)
        print('Reading degree ranks.')
        with open(ranked_fn, 'r') as f:
            book_id_to_degree_rank = json.load(f)
        print('Reading sorted degrees.')
        with open(sorted_fn, 'r') as f:
            book_ids_sorted_by_degree = json.load(f)
        return book_id_to_degree, book_id_to_degree_rank, book_ids_sorted_by_degree

    print('Calculating degrees.')
    book_id_to_degree = {}
    for i, (book_id, users) in enumerate(book_to_users.items()):
        if i % 1000 == 0:
            print('    {}/{} books'.format(i, len(book_to_users)))
        neighbors = set([b for u in book_to_users[book_id] for b in user_to_books[u] if b != book_id])
        book_id_to_degree[book_id] = len(neighbors)
    
    print('Sorting degrees.')
    book_ids_sorted_by_degree = sorted(list(book_id_to_degree.items()), key=operator.itemgetter(1), reverse=True)
    book_id_to_degree_rank = {book_id: i for i, (book_id, degree) in enumerate(book_ids_sorted_by_degree)}
    
    print('Saving degrees.')
    with open(degree_fn, 'w') as f:
        json.dump(book_id_to_degree, f)
    print('Saving degree ranks.')
    with open(ranked_fn, 'w') as f:
        json.dump(book_id_to_degree_rank, f)
    print('Saving sorted degrees.')
    with open(sorted_fn, 'w') as f:
        json.dump(book_ids_sorted_by_degree, f)

    return book_id_to_degree, book_id_to_degree_rank, book_ids_sorted_by_degree

# edge weight is simply # of co-reviewers
# still need to reciprocate: 1 / weight for distances
def get_book_to_edges(user_to_books, book_to_users):
    fn = 'data/cached_book-id-to-weighted-edges.json'
    if os.path.exists(fn):
        print('Reading weighted edges!')
        with open(fn, 'r') as f:
            return json.load(f)
    print('Calculating weighted edges!')
    book_id_to_weighted_edges= {}
    for i, (book_id, users) in enumerate(book_to_users.items()):
        if i % 1000 == 0:
            print(i)
        
        pair_to_num_users = defaultdict(int)
        for u in book_to_users[book_id]:
            for b in user_to_books[u]:
                if b == book_id:
                    continue
                pair_to_num_users[b] += 1

        book_id_to_weighted_edges[book_id] = pair_to_num_users
    print('Saving weighted edges!')
    with open(fn, 'w') as f:
        json.dump(book_id_to_weighted_edges, f)

    return book_id_to_weighted_edges

# read in scraped top genres
def read_scraped_top_genres():
    print('Loading genres.')
    book_id_to_top_genres = {}
    with open('all-books/all_books.json', 'r') as f:
        raw_json = json.load(f)
        for d in raw_json:
            book_id_to_top_genres[d['book_id']] =  d['genres']
    return book_id_to_top_genres


