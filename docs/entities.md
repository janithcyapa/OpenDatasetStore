# Entity Management

Entities are **categories of things** you track (e.g., *subjects*, *rooms*, *sensors*). They hold metadata and serve as a reference for entries.

### Entity: Create
```python
store.create_entity(
    entity_type="subjects",
    entity_id="sub_001",
    description="John Doe",
    height_cm=180,
    weight_kg=75.5
)
```
- `entity_type` – The category name (string).
- `entity_id` – Must be unique within that type.
- `**metadata` – Any additional key‑value pairs.

### Entity: List
```python
df = store.list_entities("subjects")
display(df)
```
Returns a pandas DataFrame.

### Entity: Get
```python
info = store.get_entity("subjects", "sub_001")
```

### Entity: Edit
```python
store.edit_entity("subjects", "sub_001", weight_kg=76.0)
```

### Entity: Delete
```python
store.delete_entity("subjects", "sub_001")
```
