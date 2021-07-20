# received-similarity-via-network-distance

This is the Python code for the ACH 2021 lightning talk "Received similarity via network distance".


## Requirments

You'll need `python 3` to run this code. To install all the other requirements, like `numpy` and `gdown`, run:

```
pip install -r requirements.txt
```

## Data files

- `librarything-books/genre_matched_books_dict.json`:
The paper [Tags, Borders, and Catalogs](https://github.com/maria-antoniak/librarything-genres)
(Antoniak & al., CSCW 2021) sampled 300 books from LibraryThing for each of 20 user-labeled genres.
For eight literary genres, we attempted to match these LibraryThing
books to Goodreads IDs so we could analyze them in the
[UCSD Book Graph](https://sites.google.com/eng.ucsd.edu/ucsdbookgraph/home).
This json dictionary contains all those that we manually verified as matching.
For each genre, the number of books we were able to match is:
  - fantasy: 277
  - historical fiction: 267
  - horror: 236
  - memoir: 282
  - mystery: 278
  - romance: 270
  - science fiction: 258
  - vampires: 254

## Reproducing the results in the talk (and more)

1. Download data from the [UCSD Book Graph](https://sites.google.com/eng.ucsd.edu/ucsdbookgraph/home) into the `data` directory (\~5GB, this may take a while).

You will need the files `goodreads_interactions.csv` and `book_id_map.csv`.
You can easily download them from the terminal with `gdown`
(alternatively, you can download them from the [UCSD Book Graph's website](https://sites.google.com/eng.ucsd.edu/ucsdbookgraph/home).):

```
mkdir data
gdown https://drive.google.com/uc?id=1zmylV7XW2dfQVCLeg1LbllfQtHD2KUon -O data/goodreads_interactions.csv
gdown https://drive.google.com/uc?id=1CHTAaNwyzvbi1TR08MJrJ03BxA266Yxr -O data/book_id_map.csv
```

2. For each genre, get the closest books for each sampled book.

Run `get-closest-books.py` for each genre:

```
python get-closest-books.py --genre fantasy
python get-closest-books.py --genre "historical fiction"
python get-closest-books.py --genre horror
python get-closest-books.py --genre memoir
python get-closest-books.py --genre mystery
python get-closest-books.py --genre romance
python get-closest-books.py --genre "science fiction"
python get-closest-books.py --genre vampires
```

3. Scrape user-defined genre metadata for all closest books.

First get the unique book IDs for all the closest books:

```
python save-unique-book-ids.py
```

Now scrape the metadata for these (this may take a few hours):

```
python get_book_genres.py --book_ids_path librarything-books/all-unique-books-to-scrape.txt --output_directory_path all-books
```


4. Process the results:

```
python process-all-results.py
```

It will save `average-percentage-closest-books-same-genre.pdf`,
which contains the results for all genres plotted on a bar graph.




