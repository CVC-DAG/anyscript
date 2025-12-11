# AnyScript — Training Data Guide

This guide explains how to use the provided `train_set_labels.json` metadata to prepare training inputs for both competition tracks:
- **Intra-Book Track** (page retrieval)
- **Extra-Book Track** (book retrieval)

## 📦 Metadata Format

The file `train_set_labels.json` maps authors to their books and pages:

```json
{
  "AuthorID_1": {
      "BookID_A": ["page_0001.png", "page_0002.png"],
      "BookID_B": ["page_0101.png", "page_0102.png"]
  },
  "AuthorID_2": { },
}

```
Where the path to the documents are organized as follows: `/<root_folder>/BOOK_ID/PAGE_ID.png`. 
In the intra-book tasks, authors will receive a set of queries QUERY_ID and are expected to return a similarity per PAGE_ID in the training set; where QUERY_ID and PAGE_ID are expected to be from the same book. 
In book-level retrieval, authors will receive a set of query books BOOK_QUERY_ID (multi-page) and are expected to return a similarity per BOOK_ID_N in the training set; where BOOK_QUERY_ID and BOOK_ID_N are expected to be from the same author.
