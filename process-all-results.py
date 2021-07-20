import json
import csv
from collections import defaultdict
import pandas as pd
import itertools
import argparse
import operator
import gzip
import os
import glob
import numpy as np
from book_graph_utils import *
# don't let matplotlib use xwindows
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.pylab import savefig
import seaborn as sns
sns.set_style("whitegrid")
sns.set_palette(sns.color_palette("hls", 8))

all_genres_uppercase = ['Romance', 'Fantasy', 'Historical Fiction', 'Science Fiction', 'Vampires', 'Memoir', 'Horror', 'Mystery']
all_genres = [genre.lower() for genre in all_genres_uppercase]

# the basic data from the book graph
user_to_books, book_to_users = get_cached_goodreads_events()


# read in book metadata
book_id_to_metadata = get_metadata()
# get degrees
book_id_to_degree, book_id_to_degree_rank, book_ids_sorted_by_degree = get_books_to_degrees(user_to_books, book_to_users)
# genres
book_id_to_top_genres = read_scraped_top_genres()


# save highest-degree books for human-reading and scraping genres
print('Saving highest-degree books')
book_titles_sorted_by_degree = [(book_id_to_metadata[book_id]['title'], degree) for book_id, degree in book_ids_sorted_by_degree]
df = pd.DataFrame(book_titles_sorted_by_degree, columns = ['book_id', 'degree'])
df.to_csv('./librarything-books/book-titles-sorted-by-degree.csv', index=False)
with open('librarything-books/highest-degree-top-500-books-to-scrape.txt', 'w') as f:
    f.write('\n'.join([book_id for book_id, _ in book_ids_sorted_by_degree[:500]]))

# get percentage of top-degree books in each genre
print('Baseline membership in genres for highest-degree books:')
genre_numbers = []
for genre in all_genres_uppercase:
    num_with_genre_in_top_k = 0
    for book_id, _ in book_ids_sorted_by_degree[:500]:
        top_five_genres = book_id_to_top_genres[book_id][:5]
        num_with_genre_in_top_k += int(any([genre in g for g in top_five_genres]))
    genre_numbers.append((genre, num_with_genre_in_top_k))
for genre, num in sorted(genre_numbers, key=operator.itemgetter(1), reverse=True):
    print('    {}: {} ({:.2f}%)'.format(genre, num, num / 500 * 100))


genre_to_percent_mean = {}
genre_to_percent_std = {}

genre_mean_std = []

tidy_percents = []
print('Getting average percentage of closest books that are in the same genre')
for genre in all_genres_uppercase:
    print('    ', genre)

    lowercase_genre = genre.lower()
    with open('librarything-books/{}-closest-books-network-distance-weighted.json'.format(lowercase_genre), 'r') as f:
        book_id_to_closest = json.load(f)

    percents = []
    for book_id, closest in book_id_to_closest.items():
        # get whether the same genre is in top k of each top 10 neighbor's user shelves
        num_with_genre_in_top_k = 0
        num_neighbors_checked = 10
        for i, (target_book_id, _, _) in enumerate(closest[:num_neighbors_checked]):
            top_five_genres = book_id_to_top_genres[target_book_id][:5]
            num_with_genre_in_top_k += int(any([genre in g for g in top_five_genres]))
        percent_with_genre_in_top_k = num_with_genre_in_top_k / num_neighbors_checked
        percents.append(percent_with_genre_in_top_k * 100)
        tidy_percents.append([lowercase_genre, percent_with_genre_in_top_k])
    genre_to_percent_mean[lowercase_genre] = np.mean(percents)
    genre_to_percent_std[lowercase_genre] = np.std(percents)
    genre_mean_std.append((lowercase_genre, np.mean(percents), np.std(percents)))
print('Sorted average percentage of closest books that are in the same genre:')
sorted_genre_tuples = sorted(genre_mean_std, key=operator.itemgetter(1), reverse=True)
for genre, mean, std in sorted_genre_tuples:
    print('    {}: {:.2f} ± {:.2f} std'.format(genre, mean, std))
genre_order = [genre for genre, _, _ in sorted_genre_tuples]

# plot results!
percents_df = pd.DataFrame(tidy_percents, columns=['Genre', 'Percentage of closest books in same genre'])
print(percents_df.head())
print(genre_order)
plt.figure(figsize=(14,2.4))
ax = sns.barplot(x='Genre', y='Percentage of closest books in same genre', data=percents_df, order=genre_order, palette=hypothesis_color_order)
ax.set_ylim((0,1))
ax.set_xlabel('Genre', fontsize=16)
ax.set_ylabel('Percentage of closest\nbooks in same genre', fontsize=16)
ax.set_xticklabels(ax.get_xticklabels(), fontsize=14)
ax.set_yticklabels(ax.get_yticklabels(), fontsize=14)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.grid(b=True, which='minor', axis='y')
ax.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.1))
bar_labels = ['{:.1f}%'.format(m) for _, m, _ in sorted_genre_tuples]
for rect, label in zip(ax.patches, bar_labels):
    ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 0.06, label,
            ha='center', va='bottom', fontsize=14)
savefig('./average-percentage-closest-books-same-genre.pdf', bbox_inches='tight')
plt.close()

print('Getting average percentage of closest 1-hop neighbor books that are in the same genre')
genre_mean_std = []
for genre in all_genres_uppercase:
    print('    ', genre)

    lowercase_genre = genre.lower()
    with open('librarything-books/{}-most-coreviewed-neighbors.json'.format(lowercase_genre), 'r') as f:
        book_id_to_most_coreviewed_neighbors = json.load(f)

    percents = []
    for book_id, coreviewed in book_id_to_most_coreviewed_neighbors.items():
        # get whether the same genre is in top k of each top 10 neighbor's user shelves
        num_with_genre_in_top_k = 0
        num_neighbors_checked = 10
        for i, (target_book_id, _) in enumerate(coreviewed[:num_neighbors_checked]):
            top_five_genres = book_id_to_top_genres[target_book_id][:5]
            num_with_genre_in_top_k += int(any([genre in g for g in top_five_genres]))
        percent_with_genre_in_top_k = num_with_genre_in_top_k / num_neighbors_checked * 100
        percents.append(percent_with_genre_in_top_k)
    genre_to_percent_mean[genre] = np.mean(percents)
    genre_to_percent_std[genre] = np.std(percents)
    genre_mean_std.append((genre, np.mean(percents), np.std(percents)))
print('Sorted average percentage of closest 1-hop neighbor books that are in the same genre:')
for genre, mean, std in sorted(genre_mean_std, key=operator.itemgetter(1), reverse=True):
    print('    {}: {:.2f} ± {:.2f} std'.format(genre, mean, std))

# get this intersection across all genres
# row in the csv: title, # times top total, # times top in romance, # times top in fantasy, ...
totals = {}
# book_id_to_number_of_times_in_top_k[book_id][genre]
book_id_to_number_of_times_in_top_k = defaultdict(lambda: defaultdict(int))
for genre in all_genres:
    print('Getting results for {}'.format(genre))
    with open('librarything-books/{}-closest-books-network-distance-weighted.json'.format(genre), 'r') as f:
        book_id_to_closest = json.load(f)
    totals[genre] = len(book_id_to_closest)
    # which books are near-neighbors of all of the sampled books???
    for source_book_id, closest in book_id_to_closest.items():
        for book_id, distance, num_hops in closest[:10]:
            book_id_to_number_of_times_in_top_k[book_id][genre] += 1
book_id_tuples = [tuple([book_id_to_metadata[b]['title'], sum(genre_dict.values())] + ['{} ({:.1f}%)'.format(genre_dict[g], genre_dict[g] / totals[g] * 100) for g in all_genres]) for b, genre_dict in book_id_to_number_of_times_in_top_k.items()]
book_id_tuples.sort(key=operator.itemgetter(1), reverse=True)
df = pd.DataFrame(book_id_tuples[:500], columns = ['book_id', 'total'] + all_genres)
df.to_csv('./librarything-books/top-10-closest-books-all-genres.csv', index=False)

# now sort by top for each genre
book_id_tuples = [tuple([book_id_to_metadata[b]['title'], sum(genre_dict.values())] + [genre_dict[g] / totals[g] * 100 for g in all_genres]) for b, genre_dict in book_id_to_number_of_times_in_top_k.items()]
for i, genre in enumerate(all_genres):
    print('Sorting by {}'.format(genre))
    all_rows = book_id_tuples.copy()
    all_rows.sort(key=operator.itemgetter(2 + i), reverse=True)
    # now stringify percentage floats and take the top 500
    all_genre_strings = [tuple('{:.0f}%'.format(percent) for percent in row[2:]) for row in all_rows[:500]]
    rows = [row[:2] + genre_strings for row, genre_strings in zip(all_rows[:500], all_genre_strings)]
    df = pd.DataFrame(rows, columns = ['book_id', 'total'] + all_genres)
    df.to_csv('./librarything-books/top-10-closest-books-all-genres_sorted-by-{}.csv'.format(genre), index=False)















