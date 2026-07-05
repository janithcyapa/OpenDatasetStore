# OpenDatasetStore

**A universal, plug-and-play manager for organizing research datasets on Google Drive**  
Bridge the gap between raw storage and Google Colab with an automated, JSON-indexed manifest system, backed by a real-time `fsspec` Virtual File System.

`OpenDatasetStore` replaces ad‑hoc file management with a **metadata‑driven manifest**. You define **entities** (like *subjects*, *rooms*, *devices*) and **entries** (like *experiments*, *measurements*, *trials*) once, then the library handles organized folder structure, consistent naming, and linking between raw and processed files.

---

## Documentation

We have split the documentation into comprehensive guides. Please refer to the sections below:

1. [Installation](docs/installation.md) - How to install the package in Colab or locally.
2. [Initialization](docs/initialization.md) - How to initialize the store (Local vs Colab vs GDrive API).
3. [Entities](docs/entities.md) - How to manage categories of subjects/items.
4. [Entries](docs/entries.md) - How to manage raw datasets and recordings.
5. [Related Files](docs/related_files.md) - How to handle large non-tabular files like videos.
6. [Processed Data](docs/processed_data.md) - How to link processed Parquet data back to your entries.
7. [Data Inspection](docs/data_inspection.md) - Built-in data sanitation and inspection tools.
8. [Plotting](docs/plotting.md) - How to use the global Plotly theme and DataPlotter utility.

---

Now you have a complete, reproducible, and shareable dataset manager tailored for research workflows. For questions or contributions, open an issue on the repository.
