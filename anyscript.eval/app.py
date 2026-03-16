import json
import pandas as pd
import torch
import torchmetrics.functional.retrieval as F
from pathlib import Path
import numpy as np
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import os

from evaluation_functions import *

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this in production
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['PARTICIPANTS_FOLDER'] = './participants'

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PARTICIPANTS_FOLDER'], exist_ok=True)

# Load configuration files
IDEAL_RANKNGS = "ideal_rankings_nDCG.json"
IDEAL_RANKNGS_BOOKS = "ideal_rankings_nDCG_books.json"
LUT_PAGES_PATH = "lup_pages_queries.json"
LUT_BOOKS_PATH = "lup_books_queries.json"
LUT_AUTH = 'confidential_authorship_data_do_not_share.json'
LUT_FULL_CATALOG = "full_catalog_data.json"

def load_json(path):
    with open(path, "rb") as f:
        info = json.load(f)
    return info

# Load catalogs at startup
try:
    lut_full_catalog = load_json(LUT_FULL_CATALOG)
    lut_pages = load_json(LUT_PAGES_PATH)
    lut_books = load_json(LUT_BOOKS_PATH)
    lut_aut = load_json(LUT_AUTH)
    ideal_rankings = load_json(IDEAL_RANKNGS)
    ideal_rankings_books = load_json(IDEAL_RANKNGS_BOOKS)

    # Build lookup maps
    book_id_to_author = {}
    book_id_pages = {}
    for auth, list_books in lut_aut.items():
        for (book, list_pages) in list_books.items():
            book_id_to_author[book.strip()] = auth
            book_id_pages[book.strip()] = list_pages

    print("Configuration loaded successfully")
except Exception as e:
    print(f"Error loading configuration: {e}")
    book_id_to_author = {}
    book_id_pages = {}

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_csv_format(df, track_type):
    """
    Validate CSV format for security and correctness.
    track_type: 'books' or 'pages'
    """
    required_columns = {'query_image', 'retrieved_image', 'similarity'}

    # Check for required columns
    if not required_columns.issubset(df.columns):
        return False, f"Missing required columns. Need: {required_columns}"

    # Check for extra columns
    if set(df.columns) != required_columns:
        return False, f"Extra columns found. Only allowed: {required_columns}"

    # Check data types
    if not pd.api.types.is_string_dtype(df['query_image']):
        return False, "query_image must be string type"

    if not pd.api.types.is_string_dtype(df['retrieved_image']):
        return False, "retrieved_image must be string type"

    if not pd.api.types.is_numeric_dtype(df['similarity']):
        return False, "similarity must be numeric type"

    # Check for empty dataframe
    if len(df) == 0:
        return False, "CSV file is empty"

    # Basic security: check for suspicious content
    for col in ['query_image', 'retrieved_image']:
        if df[col].str.contains(r'[<>{}]', regex=True).any():
            return False, f"Invalid characters detected in {col}"

    # Check similarity values are reasonable
    if (df['similarity'] < -1).any() or (df['similarity'] > 1).any():
        return False, "Similarity values should be between -1 and 1"

    return True, "Valid"

def compute_metrics(df, track_type):
    """
    Compute metrics for the given track.
    track_type: 'books' or 'pages'
    """
    try:
        results = {}

        if track_type == 'books':
            # MAP and Recall at k
            map_at_k, recall_at_k = compute_map_recall_at_k(
                df, k=10, queries_map=None, evaluate_page=False,
                book_to_author_map=book_id_to_author, book_to_pages_map=book_id_pages
            )

            # nDCG
            ndcg_at_k = compute_nDCG(
                df, ideal_rankings_books, k=10,
                book_to_author=book_id_to_author,
                lut_full_catalog=lut_full_catalog,
                queries_map=lut_books
            )

            results = {
                'map@10': float(map_at_k),
                'recall@10': float(recall_at_k),
                'ndcg@10': float(ndcg_at_k)
            }

        elif track_type == 'pages':
            # MAP and Recall at k
            map_at_k, recall_at_k = compute_map_recall_at_k(
                df, k=10, queries_map=None, evaluate_page=True,
                book_to_author_map=book_id_to_author, book_to_pages_map=book_id_pages
            )

            # nDCG
            ndcg_at_k = compute_nDCG(
                df, ideal_rankings, k=10,
                book_to_author=book_id_to_author,
                lut_full_catalog=lut_full_catalog,
                queries_map=lut_pages
            )

            results = {
                'map@10': float(map_at_k),
                'recall@10': float(recall_at_k),
                'ndcg@10': float(ndcg_at_k)
            }

        return results, None

    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Validate team info
    team_name = request.form.get('team_name', '').strip()
    email = request.form.get('email', '').strip()

    if not team_name or not email:
        flash('Team name and email are required', 'error')
        return redirect(url_for('index'))

    # Basic email validation
    if '@' not in email or '.' not in email:
        flash('Invalid email format', 'error')
        return redirect(url_for('index'))

    # Check if at least one file is uploaded
    books_file = request.files.get('books_csv')
    pages_file = request.files.get('pages_csv')

    if not books_file and not pages_file:
        flash('At least one CSV file must be uploaded', 'error')
        return redirect(url_for('index'))

    results = {
        'submission_id': str(uuid.uuid4()),
        'team_name': team_name,
        'email': email,
        'timestamp': datetime.now().isoformat(),
        'tracks': {}
    }

    # Process books track
    if books_file and books_file.filename and allowed_file(books_file.filename):
        try:
            df_books = pd.read_csv(
                books_file,
                sep=",",
                dtype={'query_image': str, 'retrieved_image': str, 'similarity': float}
            )

            valid, msg = validate_csv_format(df_books, 'books')
            if not valid:
                flash(f'Books CSV validation error: {msg}', 'error')
                return redirect(url_for('index'))

            metrics, error = compute_metrics(df_books, 'books')
            if error:
                flash(f'Books metrics computation error: {error}', 'error')
                return redirect(url_for('index'))

            results['tracks']['books'] = metrics

        except Exception as e:
            flash(f'Error processing books CSV: {str(e)}', 'error')
            return redirect(url_for('index'))

    # Process pages track
    if pages_file and pages_file.filename and allowed_file(pages_file.filename):
        try:
            df_pages = pd.read_csv(
                pages_file,
                sep=",",
                dtype={'query_image': str, 'retrieved_image': str, 'similarity': float}
            )

            valid, msg = validate_csv_format(df_pages, 'pages')
            if not valid:
                flash(f'Pages CSV validation error: {msg}', 'error')
                return redirect(url_for('index'))

            metrics, error = compute_metrics(df_pages, 'pages')
            if error:
                flash(f'Pages metrics computation error: {error}', 'error')
                return redirect(url_for('index'))

            results['tracks']['pages'] = metrics

        except Exception as e:
            flash(f'Error processing pages CSV: {str(e)}', 'error')
            return redirect(url_for('index'))

    # Save results
    result_path = Path(app.config['PARTICIPANTS_FOLDER']) / f"{results['submission_id']}.json"
    with open(result_path, 'w') as f:
        json.dump(results, f, indent=2)
    try:
        df_books.to_csv(f'uploads/books_{results["submission_id"]}.csv')
    except:
        pass

    try:
        df_pages.to_csv(f'uploads/pages_{results["submission_id"]}.csv')
    except:
        pass
        
    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
