# OpenDatasetStore - Complete User Guide

**A universal, plug-and-play manager for organizing research datasets on Google Drive**  
Bridge the gap between raw storage and Google Colab with an automated, JSON-indexed manifest system.

---

## Table of Contents
1. [Overview & Philosophy](#overview--philosophy)
2. [Setup & Installation](#setup--installation)
3. [Initialization](#initialization)
4. [Directory Structure](#directory-structure)
5. [Entity Management](#entity-management)
   - [Create](#entity-create)
   - [List](#entity-list)
   - [Get](#entity-get)
   - [Edit](#entity-edit)
   - [Delete](#entity-delete)
6. [Entry Management](#entry-management)
   - [Create (Interactive)](#entry-create-interactive)
   - [Create (From DataFrame)](#entry-create-from-dataframe)
   - [List Entries](#entry-list)
   - [Get Entry Metadata](#entry-get-metadata)
   - [Get Raw Data](#entry-get-raw-data)
   - [Edit Entry](#entry-edit)
   - [Delete Entry](#entry-delete)
7. [Processed Data](#processed-data)
   - [Add Processed Data](#add-processed-data)
   - [Replace Processed Data](#replace-processed-data)
   - [Retrieve Processed Data](#retrieve-processed-data)
8. [Advanced: Naming Patterns](#advanced-naming-patterns)
9. [Utility: Quick Start](#utility-quick-start)
10. [Full Example Workflow](#full-example-workflow)

---

## Overview & Philosophy

`OpenDatasetStore` replaces ad‑hoc file management with a **metadata‑driven manifest**. You define **entities** (like *subjects*, *rooms*, *devices*) and **entries** (like *experiments*, *measurements*, *trials*) once, then the library handles:

- **Organized folder structure**  
- **Consistent naming conventions**  
- **Raw data (CSV) and processed data (Parquet) linking**  
- **Automatic timestamping and ID generation**  
- **CRUD operations with interactive Google Colab uploads**

Everything is stored as plain JSON indexes and CSV/Parquet files – human‑readable and portable.

---

## Setup & Installation

The store is a single Python file. In Google Colab:

```python
# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Download the latest store manager
!wget -q -O open_dataset_store.py https://raw.githubusercontent.com/YOUR_REPO/open_dataset_store/main/open_dataset_store.py

from open_dataset_store import OpenDatasetStore
```

If you are running locally (without Colab), you can skip the `drive.mount()` and simply provide a local path.

---

## Initialization

Create an instance by specifying the **base directory** on Drive. Optionally, customise the naming patterns.

```python
store = OpenDatasetStore(
    base_dir='/content/drive/MyDrive/MyResearchData',
    entry_id_format="entry_{type}_{num:04d}",          # Default:  {type}_{num:06d}
    raw_filename_format="{entry_id}_{entity_id}_{ts}_{original}",
    processed_filename_format="{entry_id}_{tag}.parquet"
)
```

- `base_dir` – Root folder. Sub‑folders will be created automatically.
- `entry_id_format` – Template for auto‑generated entry IDs.  
  Placeholders: `{type}` (entry type name, e.g., `experiments`), `{num}` (auto‑increment integer).
- `raw_filename_format` – Template for raw CSV files.  
  Placeholders: `{entry_id}`, `{entity_id}`, `{ts}` (*YYYYMMDD_HHMMSS*), `{original}` (original upload name).
- `processed_filename_format` – Template for processed Parquet files.  
  Placeholders: `{entry_id}`, `{tag}`.

All format strings use Python’s `str.format()`.

---

## Directory Structure

After initialization, the following directories are created (or verified) inside `base_dir`:

```
MyResearchData/
├── index/
│   ├── entities_subjects.json       # One file per entity type
│   ├── entries_experiments.json    
│   └── ...
├── raw_data/
│   └── experiments/                # Organised by entry type
│       └── exp_001_sub_001_20260507_140000_myfile.csv
├── processed_data/
│   └── experiments/
│       └── filtered/
│           └── exp_001_filtered.parquet
│       └── gnn_output/
│           └── exp_001_gnn_output.parquet
```

---

## Entity Management

Entities are **categories of things** you track (e.g., *subjects*, *rooms*, *sensors*). They hold metadata and serve as a reference for entries.

### Entity: Create
```python
store.create_entity(
    entity_type="subjects",
    entity_id="sub_001",
    description="John Doe",
    height_cm=180,
    weight_kg=75.5,
    max_lift_kg=120,
    dominant_hand="right"
)
```
- `entity_type` – The category name (string). A new JSON file will be created if needed.
- `entity_id` – **Required**, must be unique within that type.
- `description` – Optional, but recommended.
- `**metadata` – Any additional key‑value pairs (e.g., `height_cm`, `weight_kg`). No schema restrictions.

### Entity: List
```python
df = store.list_entities("subjects")
display(df)   # In Colab this shows an interactive table
```
Returns a **pandas DataFrame** with one row per entity. Columns: `entity_id`, `description`, plus all your custom metadata fields.

### Entity: Get
```python
info = store.get_entity("subjects", "sub_001")
# Returns the full dictionary, e.g.:
# {'description': 'John Doe', 'height_cm': 180, 'weight_kg': 75.5, ...}
```

### Entity: Edit
```python
store.edit_entity(
    "subjects",
    "sub_001",
    description="John Doe (updated)",   # optional
    weight_kg=76.0,                     # optional metadata update
    new_field="some value"              # add a new field
)
```
You can pass `description=None` to leave it unchanged. Any `**updates` will merge into the existing metadata.

### Entity: Delete
```python
store.delete_entity("subjects", "sub_001")
```
**Important:** This only removes the entity from the JSON index. Existing entries and files are **not** automatically deleted; you should handle them separately if needed.

---

## Entry Management

Entries represent **actual recordings / trials / measurements**. They are linked to an entity and contain a raw CSV plus processed derivatives.

### Entry: Create (Interactive)
*Works only in Google Colab (uses the upload widget).*

```python
store.create_entry_interactive(
    entry_type="experiments",
    entity_id="sub_001",
    description="Walking trial with 5 kg backpack",
    # Optional:
    entry_id="exp_001",          # if omitted, auto‑generated
    timestamp="2026-05-07 14:00",# if omitted, current UTC time
    backpack_weight_kg=5,
    terrain="flat"
)
```
- A file picker appears – select your raw CSV.
- The CSV is saved according to `raw_filename_format`.
- Returns the `entry_id` (useful if auto‑generated).

### Entry: Create (From DataFrame)
Use when you already have a pandas DataFrame (no upload widget).

```python
import pandas as pd
df = pd.read_csv("/content/drive/MyDrive/local_file.csv")

entry_id = store.create_entry_from_df(
    entry_type="experiments",
    entity_id="sub_001",
    df=df,
    original_filename="local_file.csv",   # used for naming placeholder
    entry_id="exp_002",                  # optional
    timestamp="2026-05-07 15:00",        # optional
    description="Resting baseline",
    extra_meta="value"                   # any additional metadata
)
```

### Entry: List
```python
df = store.list_entries("experiments")
display(df)
```
The DataFrame shows: `entry_id`, `entity_id`, `timestamp`, `description`, `raw_csv_path`, `processed_files` (summary), and any extra metadata columns.

### Entry: Get Metadata
```python
meta = store.get_entry("experiments", "exp_001")
```
Returns the full dictionary stored in the index (including raw file path, processed file mappings, and all custom metadata).

### Entry: Get Raw Data
```python
raw_df = store.get_entry_raw_data("experiments", "exp_001")
# raw_df is a pandas DataFrame ready for processing
```

### Entry: Edit
```python
store.edit_entry(
    "experiments",
    "exp_001",
    description="Updated description",
    new_metadata_field="important note"
)
```
The raw CSV and processed files **remain untouched**. Only the metadata index is updated.

### Entry: Delete
```python
store.delete_entry("experiments", "exp_001", ask_confirm=True)
```
- If `ask_confirm=True` (default), you’ll be prompted in the terminal.
- This **deletes the raw CSV, all processed files, and the index entry**.  
- **Cannot be undone** – make sure you’ve exported any needed data first.

---

## Processed Data

When you generate derived data (filtered, model outputs, statistics, etc.), attach them to an entry using a **tag**.

### Add Processed Data
```python
# Suppose filtered_df is your cleaned/processed DataFrame
store.add_processed_data(
    entry_type="experiments",
    entry_id="exp_001",
    tag="filtered",
    df=filtered_df,
    description="Applied low‑pass Butterworth filter",
    cutoff_freq_hz=10
)
```
- Saves the DataFrame as Parquet (efficient, fast).
- Links it to the entry’s `processed_files` dictionary.
- Extra metadata for the processed set is stored under `processed_metadata`.

### Replace Processed Data
```python
store.replace_processed_data(
    entry_type="experiments",
    entry_id="exp_001",
    tag="filtered",
    df=new_filtered_df,
    description="Updated filter parameters"
)
```
Overwrites the Parquet file and updates the metadata. The tag must already exist (use `add` first).

### Retrieve Processed Data
```python
filtered_df = store.get_entry_processed_data(
    "experiments", "exp_001", "filtered"
)
```
Loads the Parquet file back into a pandas DataFrame.

---

## Advanced: Naming Patterns

You control how files are named by customising the three format strings during initialisation.

### Default formats:
- **Entry ID**: `{type}_{num:06d}` → `experiments_000001`
- **Raw file**: `{entry_id}_{entity_id}_{ts}_{original}` →  
  `experiments_000001_sub_001_20260507_140500_myfile.csv`
- **Processed file**: `{entry_id}_{tag}.parquet` →  
  `experiments_000001_filtered.parquet`

### Examples of customisation:
```python
# Minimal names, just ID + tag
store = OpenDatasetStore(
    base_dir=...,
    entry_id_format="exp_{num:03d}",
    raw_filename_format="{entry_id}.csv",
    processed_filename_format="{entry_id}_{tag}.parquet"
)

# Include entity type in processed filename
processed_filename_format="{entry_type}_{entity_id}_{entry_id}_{tag}.parquet"
```
Placeholders are replaced **literally** – any missing keys will cause an error. Valid placeholders for each format are listed in the initialisation docstring.

---

## Utility: Quick Start

For the most common use‑case, you can use `quick_start`:

```python
from open_dataset_store import quick_start
store = quick_start('/content/drive/MyDrive/MyDataset')
```
This sets:
- `entry_id_format` → `"entry_{num:04d}"`
- `raw_filename_format` → `"{entry_id}_{entity_id}_{ts}_{original}"`
- `processed_filename_format` → `"{entry_id}_{tag}.parquet"`

---

## Full Example Workflow

```python
# 1. Mount Drive and import
from google.colab import drive
drive.mount('/content/drive')
from open_dataset_store import OpenDatasetStore

store = OpenDatasetStore('/content/drive/MyDrive/WearableBiomechanics')

# 2. Create a subject
store.create_entity("subjects", "sub_001", "John Doe", height_cm=180, weight_kg=78.5)

# 3. List subjects
display(store.list_entities("subjects"))

# 4. Upload an experiment (interactive – only in Colab)
exp_id = store.create_entry_interactive(
    "experiments", "sub_001",
    description="Walking trial",
    activity="fast_walking"
)
# exp_id could be 'experiments_000001'

# 5. Retrieve raw data for processing
raw = store.get_entry_raw_data("experiments", exp_id)

# 6. Do some processing
filtered = raw.copy()   # replace with actual processing
filtered['accel_x'] = filtered['accel_x'].rolling(5).mean()

# 7. Save processed data
store.add_processed_data("experiments", exp_id, "kalman_filtered", filtered)

# 8. List experiments – see processed files column
display(store.list_entries("experiments"))

# 9. Later, reload processed data
filtered_reloaded = store.get_entry_processed_data("experiments", exp_id, "kalman_filtered")

# 10. Edit metadata if needed
store.edit_entry("experiments", exp_id, description="Updated after filter tweaking")
```

---

## Tips & Best Practices

- **Entity types and entry types** are free‑form strings. Use plural names like `subjects`, `rooms`, `sessions` for clarity.
- **Custom metadata** is completely flexible. You can store strings, numbers, lists, even nested dicts.
- **Processed data tags** should be short, descriptive, and snake_cased: `filtered`, `gnn_posture`, `statistics`.
- **Deleting an entry** removes all associated files. Consider extracting data first with `get_entry_raw_data` or `get_entry_processed_data`.
- The store works **outside Colab** too – just skip interactive upload and use `create_entry_from_df`.

---

Now you have a complete, reproducible, and shareable dataset manager tailored for research workflows. For questions or contributions, open an issue on the repository.
