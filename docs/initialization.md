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

## 5. Dataset Summary
Once you have initialized the store, you can get a quick overview of all entities and entries currently stored in your dataset by calling the `summary()` method:

```python
store = quick_start('./my_local_dataset', backend='local')
summary_stats = store.summary()
```

This will print a formatted summary to your console detailing the base directory, backend in use, and the counts for each entity and entry type. It also returns a dictionary containing these statistics for programmatic use.

You can also include storage statistics directly in this overview by passing `include_storage=True`:
```python
summary_stats = store.summary(include_storage=True)
```

## 6. Storage & File Size Summary
To inspect the physical disk or Google Drive storage utilized by your dataset store, use `storage_summary()` (or its alias `file_size_summary()`):

### 6.1 Total Size (Default / No Parameters)
Calling `storage_summary()` with no parameters prints and returns the total storage footprint and file count:

```python
storage_stats = store.storage_summary()
```

Output:
```text
💾 Storage Summary
=================================================================
Base Directory : ./my_local_dataset
Backend        : local
Total Storage  : 14.25 MB (14,942,208 bytes)
Total Files    : 42
=================================================================
```

### 6.2 Folder Breakdown (`by_folder=True`, `depth`)
Set `by_folder=True` to inspect storage distribution across directories. Use the `depth` parameter to specify how many subfolder levels to group by:

- `depth=None` (default when `by_folder=True`): Summarizes across **all** subfolder levels.
- `depth=1`: Groups storage by top-level directories (`raw_data`, `processed_data`, `index`, `related_files`, etc.).
- `depth=2`, `depth=3`, etc.: Groups storage up to the specified folder depth.

```python
# All subfolder levels
store.storage_summary(by_folder=True)

# Top-level folders only (depth=1)
store.storage_summary(by_folder=True, depth=1)

# Depth can also be passed directly
store.storage_summary(depth=2)
```

Output:
```text
📁 Folder Breakdown (Depth: 1)
-----------------------------------------------------------------
Folder                               Size    Files    % Store
-----------------------------------------------------------------
processed_data                    8.00 MB       10      56.1%
raw_data                          4.50 MB       20      31.6%
related_files                     1.70 MB        2      11.9%
index                            50.00 KB       10       0.4%
=================================================================
```

### 6.3 File Type Breakdown (`by_file_type=True`)
Analyze storage consumption by file extension (e.g., `.parquet`, `.csv`, `.json`, `.mp4`):

```python
store.storage_summary(by_file_type=True)
```

Output:
```text
📄 File Type Breakdown
-----------------------------------------------------------------
File Type                            Size    Files    % Store
-----------------------------------------------------------------
.parquet                          8.00 MB       10      56.1%
.csv                              4.50 MB       20      31.6%
.mp4                              1.70 MB        2      11.9%
.json                            50.00 KB       10       0.4%
=================================================================
```

### 6.4 Combined Summary & Additional Options
Combine both breakdowns or export results directly as a pandas DataFrame:

```python
# Both folder and file type breakdowns
store.storage_summary(by_folder=True, depth=2, by_file_type=True)

# Format sizes in specific units ('MB', 'GB', 'KB', 'B')
store.storage_summary(by_folder=True, unit="MB")

# Return results as a pandas DataFrame (without printing)
df = store.storage_summary(by_folder=True, as_df=True, print_summary=False)

# Standalone function invocation
from open_dataset_store import storage_summary
storage_summary('./my_local_dataset', by_folder=True, depth=1)
```
