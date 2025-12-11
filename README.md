# AnyScript — Training Data Guide

This guide explains how to use the provided `train_set_labels.json` metadata to prepare training inputs for both competition tracks:
- **Intra-Book Track** (page retrieval)
- **Extra-Book Track** (book retrieval)

## 📦 Metadata Format

The file `train_set_labels.json` maps authors to their books and pages:

```json
{
  "AuthorID_1": {
      "BookID_A": ["page_0001", "page_0002", ...],
      "BookID_B": ["page_0101", "page_0102", ...]
  },
  "AuthorID_2": { ... },
  ...
}
