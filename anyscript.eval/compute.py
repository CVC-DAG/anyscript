
import json
import pandas as pd
import torchmetrics.functional.retrieval as F
from pathlib import Path
import numpy as np
import torch


from evaluation_functions import *


def load_json(path):
    with open(path, "rb") as f:
        info = json.load(f)

    return info


IDEAL_RANKNGS = "ideal_rankings_nDCG.json"
IDEAL_RANKNGS_BOOKS = "ideal_rankings_nDCG_books.json"
LUT_PAGES_PATH = "lup_pages_queries.json"
LUT_BOOKS_PATH = "lup_books_queries.json"
LUT_AUTH = 'confidential_authorship_data_do_not_share.json'
LUT_FULL_CATALOG = "full_catalog_data.json"

EXAMPLE_RESPONSE_BOOKS = 'dummy_evaluation_data_books.csv'
EXAMPLE_RESPONSE_PAGES = 'dummy_evaluation_data.csv'


## carregar els catàlegs
lut_full_catalog = load_json(LUT_FULL_CATALOG)
lut_pages = load_json(LUT_PAGES_PATH)
lut_books = load_json(LUT_BOOKS_PATH)


df_books = pd.read_csv(EXAMPLE_RESPONSE_BOOKS, sep=",", dtype={'query_image': str, 'retrieved_image': str, 'similarity': float})
df_pages = pd.read_csv(EXAMPLE_RESPONSE_PAGES, sep=",", dtype={'query_image': str, 'retrieved_image': str, 'similarity': float})

## Fer el match directe
lut_aut = load_json(LUT_AUTH)

book_id_to_author = {}
book_id_pages = {}
for auth, list_books in lut_aut.items():
    for (book, list_pages) in list_books.items():
        book_id_to_author[book.strip()] = auth
        book_id_pages[book.strip()] = list_pages

# A queries map és on va lo de les LUT de pagines o de books en cas de que la response sigui amb les queries originals
map_at_k, recall_at_k = compute_map_recall_at_k(df_books, k=10, queries_map=None, evaluate_page=False, book_to_author_map=book_id_to_author, book_to_pages_map=book_id_pages)

print(' THe mean recall at k book level is: ', recall_at_k)
print(' THe mean map at k book level is: ', map_at_k)


# A queries map és on va lo de les LUT de pagines o de books en cas de que la response sigui amb les queries originals
map_at_k, recall_at_k = compute_map_recall_at_k(df_pages, k=10, queries_map=None, evaluate_page=True, book_to_author_map=book_id_to_author, book_to_pages_map=book_id_pages)

print(' THe mean recall at k page level is: ', recall_at_k)
print(' THe mean map at k page level is: ', map_at_k)


## STARTING COMPUTINMG THE NDCG....

print('Starting to compute NDCG....')

ideal_rankings = load_json(IDEAL_RANKNGS)
ideal_rankings_books = load_json(IDEAL_RANKNGS_BOOKS)

ndcg_at_k = compute_nDCG(df_pages, ideal_rankings, k=10, book_to_author=book_id_to_author, lut_full_catalog=lut_full_catalog, queries_map=lut_pages)

print(' THe mean nDCG at k page level is: ', ndcg_at_k)

ndcg_at_k = compute_nDCG(df_books, ideal_rankings_books, k=10, book_to_author=book_id_to_author, lut_full_catalog=lut_full_catalog, queries_map=lut_books)

print(' THe mean nDCG at k book level is: ', ndcg_at_k)