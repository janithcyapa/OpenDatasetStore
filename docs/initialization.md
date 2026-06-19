# Initialization

The library supports two main backends: **Local** and **Google Drive API (fsspec)**.

## 1. Google Colab (Mounted Drive)
If you are in Colab and have mounted your drive:
```python
from google.colab import drive
drive.mount('/content/drive')

from open_dataset_store import quick_start
store = quick_start('/content/drive/MyDrive/MyResearchData', backend='local')
```
*Note: Because Colab mounts Drive as a local folder, we use `backend='local'`.*

## 2. Local Environment (Local Files / Google Drive Desktop)
If you are running locally and just want to save files to your hard drive, or if you use Google Drive for Desktop to sync a local folder:
```python
from open_dataset_store import quick_start
store = quick_start('./my_local_dataset', backend='local')
```

## 3. Local Environment (Direct Google Drive API)
If you want to stream files directly to/from Google Drive *without* downloading them to your hard drive, use the `gdrive` backend.
```python
from open_dataset_store import quick_start
# A browser window will open to authenticate the first time.
store = quick_start('gdrive://MyResearchData', backend='gdrive')
```

## 4. Shared Folders (Bypassing Shortcuts)
If you are collaborating with a team and the target dataset folder is a **Shared Folder**, creating a "Shortcut" in your root Drive will not work (shortcuts are treated as files, not folders). 

Instead, you can bypass the shortcut entirely by extracting the **Folder ID** of the Shared Folder from its URL (e.g. `https://drive.google.com/drive/folders/1Gqd9XGcwvtkWpsygrdWPvjLr5cuYmyNr`) and passing it directly to the store:

```python
from open_dataset_store import quick_start

# Set base_dir to empty string (or root) and provide the exact Folder ID
store = quick_start(
    base_dir='gdrive://', 
    backend='gdrive', 
    root_file_id='1Gqd9XGcwvtkWpsygrdWPvjLr5cuYmyNr'
)
```

### Authentication Details
The `gdrive` backend uses a generic set of Google API credentials to get you started immediately. When you run it for the first time, your terminal will print:
`Please visit this URL to authorize this application...`
Click the link, log in with your Google Account, and paste the code back into the terminal. It will save a token locally so you only have to do this once.

**(Optional) Custom Credentials:**
If you plan to use this heavily in production, you can supply your own `client_secrets.json`:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new Project and enable the **Google Drive API**.
3. Go to "Credentials", create an **OAuth client ID** (Desktop Application).
4. Download the JSON file, rename it to `client_secrets.json`, and place it in your working directory alongside your script. 

