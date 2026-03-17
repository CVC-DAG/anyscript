
import pandas as pd



import pandas as pd
import torchmetrics.functional.retrieval as F
from pathlib import Path
import numpy as np
import torch



def get_book_id_from_filename(filename):
    """
    Extracts BookID from a filename.
    Example: '0000215581_30.png' -> '0000215581'
    """
    return filename.split('_')[0]


def evaluate_book_level(predictions_df, book_to_author_map, queries_map=None):
    """
    Evaluates retrieval at book level.
    Correct if retrieved_image belongs to a book written by the same author as the query book.
    
    Args:
        predictions_df: DataFrame with columns ['query_image', 'retrieved_image']
        book_to_author_map: Dict mapping BookID -> AuthorID
        queries_map: Optional dict mapping query_id to BookID if query_image is an ID
    """
    
    def is_correct(row):
        query_id = row['query_image']
        
        # Determine query book ID
        if queries_map and query_id in queries_map:
            query_book = queries_map[query_id]
        else:
             # Fallback: try to interpret query_image as filename if not in map
             query_book = get_book_id_from_filename(query_id)

        retrieved_img = row['retrieved_image']
        retrieved_book = get_book_id_from_filename(retrieved_img)
        
        # Check authors
        query_author = book_to_author_map.get(query_book)
        retrieved_author = book_to_author_map.get(retrieved_book)
        
        if query_author is None:
            print(f"Warning: Author not found for query book {query_book}")
            return False
        if retrieved_author is None:
             print(f"Warning: Author not found for retrieved book {retrieved_book}")
             return False

        return query_author == retrieved_author

    results = predictions_df.apply(is_correct, axis=1)
    accuracy = results.mean()
    print(f"Book Level Accuracy (Same Author): {accuracy:.4f}")
    return accuracy

def get_book_id_from_filename(filename):
    """
    Extracts BookID from a filename.
    Example: '0000215581_30.png' -> '0000215581'
    """
    return filename.split('_')[0]


def retrieve_page_true_relevant_documents(query_filename:str, book_to_pages_map:dict):
    book_id = get_book_id_from_filename(query_filename)
    relevant_pages = book_to_pages_map[book_id]
    return relevant_pages

def retrieve_book_true_relevant_documents(query_filename:str, book_to_author_map:dict, book_to_pages_map:dict):
    book_id = get_book_id_from_filename(query_filename)
    author = book_to_author_map[(book_id)]
    relevant_books = [book for book, auth in book_to_author_map.items() if auth == author]
    relevant_documents = []
    for book in relevant_books:
        relevant_documents.extend(book_to_pages_map[book])

    return list(relevant_documents)

def compute_map_recall_at_k(response: pd.DataFrame, k:int=100, queries_map=None, evaluate_page:bool=True, book_to_author_map:dict=None, book_to_pages_map:dict=None):
    queries = list(set(response["query_image"].tolist()))
    recall_at_k = 0.0
    map_at_k = 0.0
    for query in queries:
        filtered_response = response.loc[response["query_image"] == query]
        if queries_map and query in queries_map:
            query_img = queries_map[query]
        else:
             # Fallback: try to interpret query_image as filename if not in map
             query_img = get_book_id_from_filename(str(query))

        ## Extract relevant Documents
        if evaluate_page:
            relevant_documents = retrieve_page_true_relevant_documents(query_img, book_to_pages_map)
        else:
            assert book_to_author_map is not None, "book_to_author_map must be provided for book-level evaluation"
            relevant_documents = retrieve_book_true_relevant_documents(query_img, book_to_author_map, book_to_pages_map)

        num_relevant_documents = len(relevant_documents)

        # SORT and FILTER predictions based in K
        filtered_response_sorted = filtered_response.sort_values("similarity", ascending=False).head(k)
        total_relevant_documents_in_response = list((value in relevant_documents) for value in filtered_response_sorted["retrieved_image"])
        similarities = list(value for value in filtered_response_sorted["similarity"])
    
        #Compute Precission and Recall
        recall_at_k += (sum(total_relevant_documents_in_response) / num_relevant_documents)
        map_at_k += F.retrieval_average_precision(target=torch.tensor(total_relevant_documents_in_response), preds=torch.tensor(similarities))
        
    return (recall_at_k/len(queries)), (map_at_k / len(queries)).item()




def compute_relevance_gt(query_page,
                         candidate_page,
                         book_to_author,
                         lut_full_catalog):

    query_book = get_book_id_from_filename(query_page)
    query_author = book_to_author[query_book]

    candidate_book = get_book_id_from_filename(candidate_page)
    candidate_author = book_to_author[candidate_book]
    
    try:
        date_query = int(lut_full_catalog[query_book]["date"][0])
        date_candidate = int(lut_full_catalog[candidate_book]["date"][0])

        epoch_score = max(0.0, (20 - abs(date_query - date_candidate)) / 20)
    except:
        epoch_score = 0

    if query_book == candidate_book:
        rel = 10.0
    elif query_author == candidate_author:
        rel = 5.0
    else:
        rel = epoch_score
                        
    
    return epoch_score



def dcg_at_k(relevances, k):
    relevances = np.asarray(relevances)[:k]
    if len(relevances) == 0:
        return 0.0
    discounts = np.log2(np.arange(2, len(relevances) + 2))
    return np.sum(relevances / discounts)


def ndcg_at_k(relevances, k):
    dcg = dcg_at_k(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = dcg_at_k(ideal_relevances, k)
    return dcg / idcg if idcg > 0 else 0.0


def compute_nDCG(response,
                ideal_relevances,
                k,
                book_to_author,
                lut_full_catalog, queries_map=None):

    queries = list(set(response["query_image"]))
    total_ndcg = 0.0

    for query in queries:

        # ----- Model Ranking -----
        filtered = (
            response[response["query_image"] == query]
            .sort_values("similarity", ascending=False)
            .head(k)
        )
        if queries_map and query in queries_map:
            query_img = queries_map[query]
        else:
             # Fallback: try to interpret query_image as filename if not in map
             query_img = get_book_id_from_filename(query)
             
        predicted_relevances = [
            compute_relevance_gt(query_img,
                                 retrieved,
                                 book_to_author,
                                 lut_full_catalog)
            for retrieved in filtered["retrieved_image"]
        ]

        dcg = dcg_at_k(predicted_relevances, k)

        # ----- Ideal Ranking (Full Corpus) -----
        ideal_top_k = ideal_relevances[get_book_id_from_filename(query_img)]
        idcg = dcg_at_k(ideal_top_k, k)

        ndcg = dcg / idcg if idcg > 0 else 0.0
        total_ndcg += ndcg

    return total_ndcg / len(queries)

            



