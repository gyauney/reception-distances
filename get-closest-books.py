import json
import csv
from collections import defaultdict
import pandas as pd
import itertools
import argparse
import operator
import gzip
import os

from book_graph_utils import *

from priority_queue import PriorityQueue

parser = argparse.ArgumentParser()
parser.add_argument('--genre', type=str, required=True)
args = parser.parse_args()

def get_k_closest_books(source_book_id, user_to_books, book_to_users, k=10):
    # priority queue containing (book_id, number of hops from source) prioritized by distance
    pq = PriorityQueue()
    pq.add_or_update_vertex((source_book_id, 0), 0)

    closest_books = []
    popped_books = set()

    for i in range(k + 1):
        #print('    {}/{}'.format(i, k))
        try:
            (current_node, current_hops), current_distance = pq.pop_vertex()
        except KeyError as e:
            print(e)
            print('Only {} connected vertices.'.format(i))
            break
        # closest_books.append({'goodreads_book_id': current_node,
        #                       'distance': current_distance,
        #                       'num_hops': current_hops})
        closest_books.append((current_node, current_distance, current_hops))
        popped_books.add(current_node)
        #print('    {}th closest: {} at {} away'.format(i, current_node, current_distance))

        # now get all books reviewed by anyone who reviewed this book
        # implicit to each pair is the current_node
        #print('    Mapping neighbors to distances.')
        pair_to_num_users = defaultdict(int)
        for u in book_to_users[current_node]:
            for b in user_to_books[u]:
                if b == source_book_id:
                    continue
                pair_to_num_users[b] += 1

        neighbors = set([b for u in book_to_users[current_node] for b in user_to_books[u] if b != current_node])
        #print('    Number of neighbors: {}'.format(len(neighbors)))

        # update distances for all those books
        #print('    Updating neighbors in priority queue.')
        for book in neighbors:
            # skip edges to books that were already visited
            if book in popped_books:
                continue
            pq.add_or_update_vertex((book, current_hops + 1), current_distance + (1.0 / pair_to_num_users[book]))

        #print()



    # skip the first entry because it's just the source node
    return closest_books[1:]

# get just one-hop paths with low edge weights
# returns a list of (neighbor, num_reviewers)
def get_k_neighbors_with_most_same_reviewers(source_book_id, user_to_books, book_to_users, k=10):
    pair_to_num_users = defaultdict(int)
    for u in book_to_users[source_book_id]:
        for b in user_to_books[u]:
            if b == source_book_id:
                continue
            pair_to_num_users[b] += 1
    sorted_neighbors = sorted(list(pair_to_num_users.items()), key=operator.itemgetter(1), reverse=True)
    k_truncated = min(k, len(sorted_neighbors))
    return sorted_neighbors[:k_truncated]




# the basic data from the book graph
user_to_books, book_to_users = get_cached_goodreads_events()


# read in manually verified goodreads book ids
with open('librarything-books/genre_matched_books_dict.json', 'r') as f:
    genre_to_book_ids = json.load(f)
book_ids = genre_to_book_ids[args.genre]

book_id_to_closest = {}
book_id_to_most_coreviewed_neighbors = {}
for i, book_id in enumerate(book_ids):
    print('{} / {}'.format(i, len(book_ids)))
    if book_id not in book_to_users:
        print('Skipping book not connected in book graph: {}'.format(book_id))
        continue

    print('    Getting closest books in graph.')
    closest_books = get_k_closest_books(book_id, user_to_books, book_to_users, k=100)
    book_id_to_closest[book_id] = closest_books
    #closest_degrees = [book_id_to_degree[b] for b, _, _ in closest_books]
    #print(closest_books)

    print('    Getting most co-reviewed books.')
    most_coreviewed_neighbors = get_k_neighbors_with_most_same_reviewers(book_id, user_to_books, book_to_users, k=100)
    book_id_to_most_coreviewed_neighbors[book_id] = most_coreviewed_neighbors
    #neighbor_degrees = [book_id_to_degree[b] for b, _ in most_coreviewed_neighbors]
    #print(most_coreviewed_neighbors)
    #print(neighbor_degrees)

with open('librarything-books/{}-closest-books-network-distance-weighted.json'.format(args.genre), 'w') as f:
    json.dump(book_id_to_closest, f, indent=4)

with open('librarything-books/{}-most-coreviewed-neighbors.json'.format(args.genre), 'w') as f:
    json.dump(book_id_to_most_coreviewed_neighbors, f, indent=4)


print('Done with {}!'.format(args.genre))



