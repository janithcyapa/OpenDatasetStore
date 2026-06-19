# Entry Management

Entries represent **actual recordings / trials / measurements**. They are linked to an entity and contain a raw CSV plus processed derivatives.

### Entry: Create (Interactive)
```python
store.create_entry_interactive(
    entry_type="experiments",
    entity_id="sub_001",
    description="Walking trial"
)
```
- In Colab: A file picker appears.
- Locally: A terminal prompt asks for the absolute path of your CSV file.

### Entry: Create (From DataFrame)
```python
import pandas as pd
df = pd.DataFrame({"A": [1, 2]})

entry_id = store.create_entry_from_df(
    entry_type="experiments",
    df=df,
    original_filename="local_file.csv"
    # entity_id is optional: entity_id="sub_001"
)
```

### Entry: Get Raw Data
```python
raw_df = store.get_entry_raw_data("experiments", "exp_001")
```
When using `backend='gdrive'`, this streams the CSV *directly into memory* without saving it to disk.

### Entry: List / Get / Edit / Delete
- `store.list_entries("experiments")`
- `store.get_entry("experiments", "exp_001")`
- `store.edit_entry("experiments", "exp_001", description="Updated")`
- `store.delete_entry("experiments", "exp_001")`
