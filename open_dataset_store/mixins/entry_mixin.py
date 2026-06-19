import os
import io
import pandas as pd
from typing import Dict, Optional

try:
    # pyrefly: ignore [missing-import]
    from google.colab import files as colab_files
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

class EntryManagementMixin:
    def create_entry_interactive(
        self,
        entry_type: str,
        entity_id: Optional[str] = None,
        description: str = "",
        entry_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        **metadata,
    ) -> str:
        if IN_COLAB:
            print(f"📂 Please select the raw CSV file for entry type '{entry_type}'...")
            uploaded = colab_files.upload()
            if not uploaded:
                print("Upload cancelled.")
                return
            original_filename = list(uploaded.keys())[0]
            raw_bytes = uploaded[original_filename]
            try:
                df = pd.read_csv(io.BytesIO(raw_bytes))
            except Exception as e:
                raise ValueError(f"Error reading CSV: {e}")
        else:
            local_path = input(f"📂 Enter the absolute path to your local CSV file for entry type '{entry_type}': ").strip()
            if not os.path.exists(local_path):
                print(f"🚫 File not found: {local_path}")
                return
            original_filename = os.path.basename(local_path)
            try:
                df = pd.read_csv(local_path)
            except Exception as e:
                raise ValueError(f"Error reading CSV: {e}")

        ts = timestamp if timestamp is not None else self._generate_timestamp()
        index_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(index_path)

        if entry_id is None:
            entry_id = self._generate_entry_id(entry_type, index_data)
        else:
            if entry_id in index_data:
                raise ValueError(f"Entry ID '{entry_id}' already exists in {entry_type}.")

        raw_filename = self._build_raw_filename(entry_id, entity_id, ts, original_filename)
        raw_save_dir = f"{self.raw_dir}/{entry_type}"
        self.fs.makedirs(raw_save_dir, exist_ok=True)
        raw_full_path = f"{raw_save_dir}/{raw_filename}"
        
        with self.fs.open(raw_full_path, "wb") as f:
            df.to_csv(f, index=False)

        raw_rel_path = self._rel_path(raw_full_path)
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
        df: pd.DataFrame,
        entity_id: Optional[str] = None,
        original_filename: str = "data.csv",
        entry_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        description: str = "",
        **metadata,
    ) -> str:
        ts = timestamp if timestamp is not None else self._generate_timestamp()
        index_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(index_path)

        if entry_id is None:
            entry_id = self._generate_entry_id(entry_type, index_data)
        else:
            if entry_id in index_data:
                raise ValueError(f"Entry ID '{entry_id}' already exists in {entry_type}.")

        raw_filename = self._build_raw_filename(entry_id, entity_id, ts, original_filename)
        raw_save_dir = f"{self.raw_dir}/{entry_type}"
        self.fs.makedirs(raw_save_dir, exist_ok=True)
        raw_full_path = f"{raw_save_dir}/{raw_filename}"
        
        with self.fs.open(raw_full_path, "wb") as f:
            df.to_csv(f, index=False)

        raw_rel_path = self._rel_path(raw_full_path)
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
        index_data = self._load_json(self._get_entry_index_path(entry_type))
        entries = {k: v for k, v in index_data.items() if not k.startswith("__")}
        if not entries:
            print(f"No entries for type '{entry_type}'.")
            return pd.DataFrame()

        df = pd.DataFrame.from_dict(entries, orient="index")
        df.index.name = "entry_id"
        df.reset_index(inplace=True)
        cols_order = ["entry_id", "entity_id", "timestamp", "description", "raw_csv_path", "processed_files"]
        other_cols = [c for c in df.columns if c not in cols_order]
        df = df[cols_order + other_cols]
        return df

    def get_entry(self, entry_type: str, entry_id: str) -> Dict:
        index_data = self._load_json(self._get_entry_index_path(entry_type))
        if entry_id not in index_data:
            raise KeyError(f"Entry '{entry_id}' not found in {entry_type}.")
        return index_data[entry_id]

    def get_entry_raw_data(self, entry_type: str, entry_id: str) -> pd.DataFrame:
        meta = self.get_entry(entry_type, entry_id)
        raw_path = self._full_path(meta['raw_csv_path'])
        if not self.fs.exists(raw_path):
            raise FileNotFoundError(f"Raw file not found: {raw_path}")
        with self.fs.open(raw_path, "rb") as f:
            return pd.read_csv(f)

    def get_entry_processed_data(self, entry_type: str, entry_id: str, tag: str) -> pd.DataFrame:
        meta = self.get_entry(entry_type, entry_id)
        proc_files = meta.get("processed_files", {})
        if tag not in proc_files:
            raise KeyError(f"No processed data with tag '{tag}' for entry '{entry_id}'.")
        proc_rel_path = proc_files[tag]
        proc_full_path = self._full_path(proc_rel_path)
        if not self.fs.exists(proc_full_path):
            raise FileNotFoundError(f"Processed file not found: {proc_full_path}")
        with self.fs.open(proc_full_path, "rb") as f:
            return pd.read_parquet(f)

    def add_processed_data(
        self,
        entry_type: str,
        entry_id: str,
        tag: str,
        df: pd.DataFrame,
        **metadata,
    ) -> str:
        meta = self.get_entry(entry_type, entry_id)
        proc_save_dir = f"{self.processed_dir}/{entry_type}/{tag}"
        self.fs.makedirs(proc_save_dir, exist_ok=True)
        filename = self._build_processed_filename(entry_id, tag)
        full_path = f"{proc_save_dir}/{filename}"
        rel_path = self._rel_path(full_path)

        with self.fs.open(full_path, "wb") as f:
            df.to_parquet(f, index=False)

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
        meta = self.get_entry(entry_type, entry_id)
        if tag not in meta.get("processed_files", {}):
            raise KeyError(f"Tag '{tag}' does not exist for entry '{entry_id}'. Use add_processed_data first.")
        old_rel_path = meta["processed_files"][tag]
        old_full_path = self._full_path(old_rel_path)

        with self.fs.open(old_full_path, "wb") as f:
            df.to_parquet(f, index=False)
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
        index_data = self._load_json(self._get_entry_index_path(entry_type))
        if entry_id not in index_data:
            raise KeyError(f"Entry '{entry_id}' not found in {entry_type}.")

        if description is not None:
            index_data[entry_id]["description"] = description
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

        raw_path = self._full_path(meta['raw_csv_path'])
        if self.fs.exists(raw_path):
            self.fs.rm(raw_path)
            print(f"  - Deleted raw file: {meta['raw_csv_path']}")

        for tag, rel_path in meta.get("processed_files", {}).items():
            full_path = self._full_path(rel_path)
            if self.fs.exists(full_path):
                self.fs.rm(full_path)
                print(f"  - Deleted processed [{tag}]: {rel_path}")

        del index_data[entry_id]
        self._save_json(self._get_entry_index_path(entry_type), index_data)
        print(f"✅ Entry '{entry_id}' completely removed.")
        return entry_id
