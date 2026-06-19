# Installation

You can install `OpenDatasetStore` in any environment depending on your needs. 

## Local Environment (Standard Python)
To install locally for a regular Python project:
```bash
pip install open_dataset_store
# Or if installing from source:
pip install -e .
```
When running locally, you can choose to store files directly on your local hard drive (`backend='local'`), or use the Google Drive API (`backend='gdrive'`) to sync directly to the cloud without needing Google Drive Desktop.

## Google Colab
Colab users can install directly from the GitHub repository:
```bash
!pip install git+https://github.com/janithcyapa/OpenDatasetStore.git
```
In Colab, you typically mount your Google Drive locally, which means you should use the `backend='local'` option since the files are mounted as local paths (e.g., `/content/drive/MyDrive/`).

## Universal Real-time Cloud Streaming (fsspec)
By default, the package installs dependencies for `fsspec`, `pydrive2`, and the Google API Client. This enables the `backend='gdrive'` capability to stream files directly into Pandas without downloading whole folders.
