# Processed Data

When you generate derived data (filtered, model outputs, statistics, etc.), attach them to an entry using a **tag**.

### Add Processed Data
```python
store.add_processed_data(
    entry_type="experiments",
    entry_id="exp_001",
    tag="filtered",
    df=filtered_df
)
```
Saves the DataFrame as an optimized Parquet file.

### Replace Processed Data
```python
store.replace_processed_data("experiments", "exp_001", "filtered", new_filtered_df)
```

### Retrieve Processed Data
```python
filtered_df = store.get_entry_processed_data("experiments", "exp_001", "filtered")
```
When using `backend='gdrive'`, the Parquet file is streamed directly into Pandas memory.
