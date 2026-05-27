# open_dataset_store.py
"""
OpenDatasetStore: A universal, plug-and-play manager for organising research datasets on Google Drive.
Bridge the gap between raw storage and Google Colab with an automated, JSON-indexed manifest system.

Usage:
    from open_dataset_store import OpenDatasetStore
    store = OpenDatasetStore(base_dir='/content/drive/MyDrive/MyDataset')
    # Optional: change default patterns
    store = OpenDatasetStore(
        base_dir='/content/drive/MyDrive/MyDataset',
        entry_id_format="entry_{type}_{num:04d}",
        entity_id_format="sub_{type}_{num:04d}",
        raw_filename_format="{entry_id}_{entity_id}_{ts}_{original}",
        processed_filename_format="{entry_id}_{tag}.parquet"
    )
"""

import json
import os
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union

# Google Colab specific imports (only used for interactive upload)
try:
    from google.colab import files as colab_files
    IN_COLAB = True
except ImportError:
    IN_COLAB = False


class OpenDatasetStore:
    """Main class managing the dataset store on Google Drive."""

    # ------------------------------------------------------------------
    # Initialization & Directory Setup
    # ------------------------------------------------------------------
    def __init__(
        self,
        base_dir: str,
        entry_id_format: str = "{type}_{num:06d}",
        entity_id_format: str = "ent_{num:04d}",
        raw_filename_format: str = "{entry_id}_{entity_id}_{ts}_{original}",
        processed_filename_format: str = "{entry_id}_{tag}.parquet",
    ):
        """
        Args:
            base_dir: Full path to the dataset folder on Google Drive.
            entry_id_format: Format string for auto-generated entry IDs.
                             Use {type} (entry_type), {num} (auto-increment integer).
            entity_id_format: Format string for auto-generated entity IDs.
                              Use {type} (entity_type), {num} (auto-increment integer).
            raw_filename_format: Format string for saved raw CSV files.
                                 Available placeholders: {entry_id}, {entity_id},
                                 {ts} (YYYYMMDD_HHMMSS), {original} (original filename).
            processed_filename_format: Format string for processed Parquet files.
                                       Placeholders: {entry_id}, {tag} (processing tag).
        """
        self.base_dir = base_dir
        self.entry_id_format_str = entry_id_format
        self.entity_id_format_str = entity_id_format
        self.raw_filename_format_str = raw_filename_format
        self.processed_filename_format_str = processed_filename_format

        # Ensure directory structure exists
        os.makedirs(self.base_dir, exist_ok=True)
        self.index_dir = os.path.join(self.base_dir, "index")
        self.raw_dir = os.path.join(self.base_dir, "raw_data")
        self.processed_dir = os.path.join(self.base_dir, "processed_data")
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

        print(f"Store initialised at: {self.base_dir}")

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------
    def _get_entity_index_path(self, entity_type: str) -> str:
        return os.path.join(self.index_dir, f"entities_{entity_type}.json")

    def _get_entry_index_path(self, entry_type: str) -> str:
        return os.path.join(self.index_dir, f"entries_{entry_type}.json")

    def _load_json(self, path: str) -> Dict:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def _save_json(self, path: str, data: Dict) -> None:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _generate_timestamp(self) -> str:
        return str(int(datetime.now(timezone.utc).timestamp()))

    def _generate_entry_id(self, entry_type: str, index: Dict) -> str:
        """Generate a unique entry ID based on the configured format."""
        counter = index.get("__auto_counter__", 0)
        new_counter = counter + 1
        index["__auto_counter__"] = new_counter
        return self.entry_id_format_str.format(type=entry_type, num=new_counter)

    def _generate_entity_id(self, entity_type: str, index: Dict) -> str:
        """Generate a unique entity ID using the configurable entity_id_format."""
        counter = index.get("__entity_counter__", 0)
        new_counter = counter + 1
        index["__entity_counter__"] = new_counter
        return self.entity_id_format_str.format(type=entity_type, num=new_counter)

    def _build_raw_filename(
        self, entry_id: str, entity_id: str, timestamp: str, original_name: str
    ) -> str:
        return self.raw_filename_format_str.format(
            entry_id=entry_id,
            entity_id=entity_id,
            ts=timestamp,
            original=original_name,
        )

    def _build_processed_filename(self, entry_id: str, tag: str) -> str:
        return self.processed_filename_format_str.format(
            entry_id=entry_id, tag=tag
        )

    # ------------------------------------------------------------------
    # Entity Management (entities = subjects, rooms, ...)
    # ------------------------------------------------------------------
    def create_entity(
        self,
        entity_type: str,
        name: str = "",
        entity_id: Optional[str] = None,
        **metadata,
    ) -> str:
        """Register a new entity (e.g., subject, room).

        Args:
            entity_type: Category of entity (e.g., 'subjects', 'rooms').
            entity_id: Unique identifier for this entity.
            name: Short human‑readable name for the entity.
            **metadata: Any additional key-value pairs to store.

        Returns:
            The entity ID (user‑provided or auto‑generated).
        """
        index_path = self._get_entity_index_path(entity_type)
        data = self._load_json(index_path)

        if entity_id is None:
            entity_id = self._generate_entity_id(entity_type, data)

        if entity_id in data:
            raise ValueError(f"Entity '{entity_id}' already exists.")

        data[entity_id] = {"name": name, **metadata}
        self._save_json(index_path, data)
        print(f"Entity '{entity_id}' created in {entity_type}.")
        return entity_id

    def list_entities(self, entity_type: str) -> pd.DataFrame:
        """Return a formatted DataFrame of all entities, excluding internal counters."""
        data = self._load_json(self._get_entity_index_path(entity_type))
        
        # 1. Filter out internal keys (those starting with '__')
        entities = {k: v for k, v in data.items() if not k.startswith("__")}
        
        if not entities:
            print(f"No entities found for type '{entity_type}'.")
            return pd.DataFrame()

        # 2. Convert to DataFrame
        df = pd.DataFrame.from_dict(entities, orient="index")
        df.index.name = "entity_id"
        df.reset_index(inplace=True)
        
        # 3. Reorder columns for better readability (ID and Name first)
        cols_at_front = ["entity_id", "name"]
        # Only include columns that actually exist in the data
        existing_front = [c for c in cols_at_front if c in df.columns]
        other_cols = [c for c in df.columns if c not in existing_front]
        
        df = df[existing_front + other_cols]
        
        return df

    def get_entity(self, entity_type: str, entity_id: str) -> Dict:
        """Return the full metadata dictionary for a specific entity."""
        data = self._load_json(self._get_entity_index_path(entity_type))
        if entity_id not in data:
            raise KeyError(f"Entity '{entity_id}' not found in {entity_type}.")
        return data[entity_id]

    def edit_entity(
        self,
        entity_type: str,
        entity_id: str,
        name: Optional[str] = None,
        **updates,
    ) -> str:
        """Update metadata fields of an existing entity.

        Args:
            entity_type: Category of entity.
            entity_id: ID of the entity to update.
            name: (Optional) new name.
            **updates: Other metadata fields to update/add.

        Returns:
            The entity_id that was edited.
        """
        data = self._load_json(self._get_entity_index_path(entity_type))
        if entity_id not in data:
            raise KeyError(f"Entity '{entity_id}' not found in {entity_type}.")

        if name is not None:
            data[entity_id]["name"] = name
        data[entity_id].update(updates)
        self._save_json(self._get_entity_index_path(entity_type), data)
        print(f"Entity '{entity_id}' updated.")
        return entity_id

    def delete_entity(self, entity_type: str, entity_id: str) -> str:
        """Remove an entity and all its entries.

        Warning: This does NOT automatically delete existing entry raw/processed files.
        It only removes the entity from the index.

        Returns:
            The entity_id that was deleted.
        """
        index_path = self._get_entity_index_path(entity_type)
        data = self._load_json(index_path)
        if entity_id not in data:
            raise KeyError(f"Entity '{entity_id}' not found in {entity_type}.")

        del data[entity_id]
        self._save_json(index_path, data)
        print(f"Entity '{entity_id}' removed from {entity_type}.")
        return entity_id

    # ------------------------------------------------------------------
    # Entry Management (entries = experiments, measurements, ...)
    # ------------------------------------------------------------------
    def create_entry_interactive(
        self,
        entry_type: str,
        entity_id: str,
        description: str = "",
        entry_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        **metadata,
    ) -> str:
        """Create a new entry by interactively uploading a raw CSV file from the user.

        This method uses Google Colab's file upload widget (works only in Colab).

        Args:
            entry_type: Category of entry (e.g., 'experiments').
            entity_id: ID of the associated entity (must exist).
            description: Text describing the entry.
            entry_id: Optional explicit ID. If None, an ID is auto-generated.
            timestamp: Optional timestamp string; if None, current UTC time is used.
            **metadata: Any additional free-form metadata for this entry.

        Returns:
            The entry ID (either original or auto-generated).
        """
        if not IN_COLAB:
            raise RuntimeError(
                "Interactive upload requires Google Colab. Use create_entry_from_df() instead."
            )

        # 1. Upload file
        print(f"📂 Please select the raw CSV file for entry type '{entry_type}'...")
        uploaded = colab_files.upload()
        if not uploaded:
            print("Upload cancelled.")
            return
        original_filename = list(uploaded.keys())[0]
        raw_bytes = uploaded[original_filename]

        # 2. Read into DataFrame to verify
        try:
            df = pd.read_csv(pd.io.common.BytesIO(raw_bytes))
        except Exception as e:
            raise ValueError(f"Error reading CSV: {e}")

        # 3. Determine entry ID and timestamp
        ts = timestamp if timestamp is not None else self._generate_timestamp()
        index_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(index_path)

        if entry_id is None:
            entry_id = self._generate_entry_id(entry_type, index_data)
        else:
            if entry_id in index_data:
                raise ValueError(f"Entry ID '{entry_id}' already exists in {entry_type}.")

        # 4. Build raw file name and save
        raw_filename = self._build_raw_filename(entry_id, entity_id, ts, original_filename)
        raw_save_dir = os.path.join(self.raw_dir, entry_type)
        os.makedirs(raw_save_dir, exist_ok=True)
        raw_full_path = os.path.join(raw_save_dir, raw_filename)
        df.to_csv(raw_full_path, index=False)

        # 5. Record entry metadata
        raw_rel_path = os.path.relpath(raw_full_path, self.base_dir)
        entry_meta = {
            "entity_id": entity_id,
            "description": description,
            "timestamp": ts,
            "raw_csv_path": raw_rel_path,
            "processed_files": {},
            **metadata,
        }
        index_data[entry_id] = entry_meta
        self._save_json(index_path, index_data)
        print(f"✅ Entry '{entry_id}' created. File saved as {raw_filename}")
        return entry_id

    def create_entry_from_df(
        self,
        entry_type: str,
        entity_id: str,
        df: pd.DataFrame,
        original_filename: str = "data.csv",
        entry_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        description: str = "",
        **metadata,
    ) -> str:
        """Create a new entry by providing a DataFrame directly (no interactive upload).

        Args:
            entry_type: Category of entry.
            entity_id: Associated entity ID.
            df: Pandas DataFrame containing the raw data.
            original_filename: Used as the 'original' placeholder for naming.
            entry_id: Optional explicit ID. If None, auto-generated.
            timestamp: Optional timestamp string.
            description: Short description.
            **metadata: Additional metadata.

        Returns:
            The entry ID.
        """
        
        ts = timestamp if timestamp is not None else self._generate_timestamp()
        index_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(index_path)

        if entry_id is None:
            entry_id = self._generate_entry_id(entry_type, index_data)
        else:
            if entry_id in index_data:
                raise ValueError(f"Entry ID '{entry_id}' already exists in {entry_type}.")

        raw_filename = self._build_raw_filename(entry_id, entity_id, ts, original_filename)
        raw_save_dir = os.path.join(self.raw_dir, entry_type)
        os.makedirs(raw_save_dir, exist_ok=True)
        raw_full_path = os.path.join(raw_save_dir, raw_filename)
        df.to_csv(raw_full_path, index=False)

        raw_rel_path = os.path.relpath(raw_full_path, self.base_dir)
        entry_meta = {
            "entity_id": entity_id,
            "description": description,
            "timestamp": ts,
            "raw_csv_path": raw_rel_path,
            "processed_files": {},
            **metadata,
        }
        index_data[entry_id] = entry_meta
        self._save_json(index_path, index_data)
        print(f"✅ Entry '{entry_id}' created. File saved as {raw_filename}")
        return entry_id

    def list_entries(self, entry_type: str) -> pd.DataFrame:
        """Return DataFrame overview of all entries of a given type."""
        index_data = self._load_json(self._get_entry_index_path(entry_type))
        # Filter out internal counter key
        entries = {k: v for k, v in index_data.items() if not k.startswith("__")}
        if not entries:
            print(f"No entries for type '{entry_type}'.")
            return pd.DataFrame()

        df = pd.DataFrame.from_dict(entries, orient="index")
        df.index.name = "entry_id"
        df.reset_index(inplace=True)
        # Reorder columns for readability
        cols_order = ["entry_id", "entity_id", "timestamp", "description", "raw_csv_path", "processed_files"]
        other_cols = [c for c in df.columns if c not in cols_order]
        df = df[cols_order + other_cols]
        return df

    def get_entry(self, entry_type: str, entry_id: str) -> Dict:
        """Return full metadata for a specific entry."""
        index_data = self._load_json(self._get_entry_index_path(entry_type))
        if entry_id not in index_data:
            raise KeyError(f"Entry '{entry_id}' not found in {entry_type}.")
        return index_data[entry_id]

    def get_entry_raw_data(self, entry_type: str, entry_id: str) -> pd.DataFrame:
        """Load the raw CSV for an entry into a pandas DataFrame."""
        meta = self.get_entry(entry_type, entry_id)
        raw_path = os.path.join(self.base_dir, meta["raw_csv_path"])
        if not os.path.exists(raw_path):
            raise FileNotFoundError(f"Raw file not found: {raw_path}")
        return pd.read_csv(raw_path)

    def get_entry_processed_data(self, entry_type: str, entry_id: str, tag: str) -> pd.DataFrame:
        """Load a processed Parquet file for an entry by tag."""
        meta = self.get_entry(entry_type, entry_id)
        proc_files = meta.get("processed_files", {})
        if tag not in proc_files:
            raise KeyError(f"No processed data with tag '{tag}' for entry '{entry_id}'.")
        proc_rel_path = proc_files[tag]
        proc_full_path = os.path.join(self.base_dir, proc_rel_path)
        if not os.path.exists(proc_full_path):
            raise FileNotFoundError(f"Processed file not found: {proc_full_path}")
        return pd.read_parquet(proc_full_path)

    def add_processed_data(
        self,
        entry_type: str,
        entry_id: str,
        tag: str,
        df: pd.DataFrame,
        **metadata,
    ) -> str:
        """Save a processed DataFrame as Parquet and link it to the entry.

        Args:
            entry_type: Category of entry.
            entry_id: ID of the entry to attach to.
            tag: A short label for this processing (e.g., 'filtered', 'gnn_output').
            df: The processed DataFrame.
            **metadata: Additional metadata to store for this processed tag.

        Returns:
            The tag that was used, confirming the processed data was saved.
        """
        meta = self.get_entry(entry_type, entry_id)
        proc_save_dir = os.path.join(self.processed_dir, entry_type, tag)
        os.makedirs(proc_save_dir, exist_ok=True)
        filename = self._build_processed_filename(entry_id, tag)
        full_path = os.path.join(proc_save_dir, filename)
        rel_path = os.path.relpath(full_path, self.base_dir)

        df.to_parquet(full_path, index=False)

        meta.setdefault("processed_files", {})[tag] = rel_path
        meta.setdefault("processed_metadata", {})[tag] = metadata

        index_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(index_path)
        index_data[entry_id] = meta
        self._save_json(index_path, index_data)
        print(f"✅ Processed data '{tag}' saved and linked to entry '{entry_id}'.")
        return tag

    def replace_processed_data(
        self,
        entry_type: str,
        entry_id: str,
        tag: str,
        df: pd.DataFrame,
        **metadata,
    ) -> str:
        """Replace an existing processed dataset (overwrites file, updates metadata).

        Returns:
            The tag of the replaced dataset.
        """
        meta = self.get_entry(entry_type, entry_id)
        if tag not in meta.get("processed_files", {}):
            raise KeyError(f"Tag '{tag}' does not exist for entry '{entry_id}'. Use add_processed_data first.")
        old_rel_path = meta["processed_files"][tag]
        old_full_path = os.path.join(self.base_dir, old_rel_path)

        df.to_parquet(old_full_path, index=False)
        meta.setdefault("processed_metadata", {})[tag] = metadata

        index_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(index_path)
        index_data[entry_id] = meta
        self._save_json(index_path, index_data)
        print(f"✅ Processed data '{tag}' replaced for entry '{entry_id}'.")
        return tag

    def edit_entry(
        self,
        entry_type: str,
        entry_id: str,
        description: Optional[str] = None,
        **updates,
    ) -> str:
        """Update metadata of an entry (does not change raw/processed data files).

        Returns:
            The entry_id that was edited.
        """
        index_data = self._load_json(self._get_entry_index_path(entry_type))
        if entry_id not in index_data:
            raise KeyError(f"Entry '{entry_id}' not found in {entry_type}.")

        if description is not None:
            index_data[entry_id]["description"] = description
        # update metadata fields, but protect certain internal keys
        protected = {"raw_csv_path", "processed_files"}
        for k, v in updates.items():
            if k not in protected:
                index_data[entry_id][k] = v
        self._save_json(self._get_entry_index_path(entry_type), index_data)
        print(f"Entry '{entry_id}' metadata updated.")
        return entry_id

    def delete_entry(
        self,
        entry_type: str,
        entry_id: str,
        ask_confirm: bool = True,
    ) -> Optional[str]:
        """Delete an entry and all associated raw/processed files.

        Args:
            ask_confirm: If True, prompt the user for confirmation via input().

        Returns:
            The entry_id if deletion was successful, None if cancelled.
        """
        index_data = self._load_json(self._get_entry_index_path(entry_type))
        if entry_id not in index_data:
            raise KeyError(f"Entry '{entry_id}' not found in {entry_type}.")

        if ask_confirm:
            confirm = input(
                f"Are you sure you want to DELETE entry '{entry_id}' and ALL its files? (y/n): "
            ).strip().lower()
            if confirm != "y":
                print("Deletion cancelled.")
                return None

        meta = index_data[entry_id]

        # Delete raw CSV
        raw_path = os.path.join(self.base_dir, meta["raw_csv_path"])
        if os.path.exists(raw_path):
            os.remove(raw_path)
            print(f"  - Deleted raw file: {meta['raw_csv_path']}")

        # Delete all processed files
        for tag, rel_path in meta.get("processed_files", {}).items():
            full_path = os.path.join(self.base_dir, rel_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"  - Deleted processed [{tag}]: {rel_path}")

        # Remove entry from index
        del index_data[entry_id]
        self._save_json(self._get_entry_index_path(entry_type), index_data)
        print(f"✅ Entry '{entry_id}' completely removed.")
        return entry_id

    # ------------------------------------------------------------------
    # Related Files (Videos, Zips, etc.)
    # ------------------------------------------------------------------
    def add_related_file(self, entry_type: str, entry_id: str, label: str, local_path: str) -> str:
        """
        Moves a file to Drive with naming: {entry_id}_{entity_id}_{label}.ext
        """
        import shutil
        
        # 1. Load Index to find the linked Entity ID
        idx_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(idx_path)
        if entry_id not in index_data:
            raise KeyError(f"Entry {entry_id} not found.")
        
        # Get the entity_id (subject ID) from the experiment metadata
        entity_id = index_data[entry_id].get("entity_id", "unknown")

        # 2. Prepare Destination Path
        ext = os.path.splitext(local_path)[1]
        file_dir = os.path.join(self.base_dir, "related_files", entry_type, entry_id)
        os.makedirs(file_dir, exist_ok=True)
        
        # Strictly formatted filename: experiments_0001_sub_0001_front_video.mp4
        dest_filename = f"{entry_id}_{entity_id}_{label}{ext}"
        dest_path = os.path.join(file_dir, dest_filename)
        rel_path = os.path.relpath(dest_path, self.base_dir)

        # 3. Copy to Google Drive
        shutil.copy(local_path, dest_path)

        # 4. Update the JSON Manifest
        index_data[entry_id].setdefault("related_files", {})[label] = rel_path
        self._save_json(idx_path, index_data)
        
        print(f"📎 Attached: {dest_filename}")
        return rel_path

    def upload_related_file_interactive(self, entry_type: str, entry_id: str, label: str) -> Optional[str]:
        """Triggers a Colab upload widget and renames file based on IDs."""
        if not IN_COLAB:
            print("❌ Interactive upload only available in Google Colab.")
            return None

        print(f"📤 Select file for '{label}' (Entry: {entry_id})...")
        uploaded = colab_files.upload()
        
        if not uploaded:
            print("🚫 Upload cancelled.")
            return None

        # Process the uploaded file
        temp_filename = list(uploaded.keys())[0]
        
        try:
            # Transfer to Drive using the strict naming logic
            rel_path = self.add_related_file(entry_type, entry_id, label, temp_filename)
            return rel_path
        finally:
            # Clean up the local Colab /content/ folder
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
    def download_related_file(self, entry_type: str, entry_id: str, label: str, dest_folder: str = "/content/") -> str:
        """Copies a related file from Google Drive to the local Colab environment."""
        import shutil
        meta = self.get_entry(entry_type, entry_id)
        related = meta.get("related_files", {})
        
        if label not in related:
            raise KeyError(f"No related file with label '{label}' found for {entry_id}.")
        
        drive_path = os.path.join(self.base_dir, related[label])
        local_path = os.path.join(dest_folder, os.path.basename(drive_path))
        
        if not os.path.exists(drive_path):
            raise FileNotFoundError(f"File missing on Drive: {drive_path}")
            
        shutil.copy(drive_path, local_path)
        print(f"📥 Downloaded to: {local_path}")
        return local_path

    def delete_related_file(self, entry_type: str, entry_id: str, label: str) -> None:
        """Removes the file from Drive and deletes its entry in the JSON index."""
        idx_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(idx_path)
        
        if entry_id not in index_data or label not in index_data[entry_id].get("related_files", {}):
            print(f"⚠️ Label '{label}' not found for {entry_id}. Skipping.")
            return

        # Path on Drive
        rel_path = index_data[entry_id]["related_files"][label]
        full_path = os.path.join(self.base_dir, rel_path)

        # Delete physical file
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"🗑️ Deleted file from Drive: {rel_path}")

        # Update JSON
        del index_data[entry_id]["related_files"][label]
        self._save_json(idx_path, index_data)
        print(f"✅ Removed '{label}' from {entry_id} index.")

    def update_related_file(self, entry_type: str, entry_id: str, label: str, local_path: str) -> str:
        """Replaces an existing related file with a new version."""
        # We just delete the old one and add the new one
        self.delete_related_file(entry_type, entry_id, label)
        return self.add_related_file(entry_type, entry_id, label, local_path)

# ------------------------------------------------------------------
# Quick start helper
# ------------------------------------------------------------------
def quick_start(base_dir: str) -> OpenDatasetStore:
    """Create a store instance with sensible defaults.

    Example:
        store = quick_start('/content/drive/MyDrive/MyResearch')
    """
    return OpenDatasetStore(
        base_dir=base_dir,
        entry_id_format="entry_{num:04d}",
        entity_id_format="entity_{num:04d}",
        raw_filename_format="{entry_id}_{entity_id}_{ts}_{original}",
        processed_filename_format="{entry_id}_{tag}.parquet",
    )
