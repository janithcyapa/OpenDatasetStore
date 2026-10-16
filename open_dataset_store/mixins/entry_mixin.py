import os
import io
import ast
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
        self._safe_makedirs(raw_save_dir)
        raw_full_path = f"{raw_save_dir}/{raw_filename}"
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
        try:
            df.to_csv(tmp_path, index=False)
            self.fs.put(tmp_path, raw_full_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

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
        self._safe_makedirs(raw_save_dir)
        raw_full_path = f"{raw_save_dir}/{raw_filename}"
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
        try:
            df.to_csv(tmp_path, index=False)
            self.fs.put(tmp_path, raw_full_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

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

    def list_entries(
        self,
        entry_type: str,
        include_paths: bool = False,
        raw: bool = False,
    ) -> pd.DataFrame:
        """
        Lists all entries of a given entry_type in a clean, structured DataFrame.

        Parameters
        ----------
        entry_type : str
            The entry type (e.g. 'experiments').
        include_paths : bool, default False
            If False (default), shows file availability ('Available' / 'Not Available')
            and metadata comments without full file path columns.
            If True, adds a path column directly next to each availability column.
        raw : bool, default False
            If True, returns the unformatted dictionary/metadata DataFrame as stored in the index.

        Returns
        -------
        pd.DataFrame
            Clean DataFrame of entries with separated file availability and metadata columns.
        """
        index_data = self._load_json(self._get_entry_index_path(entry_type))
        entries = {k: v for k, v in index_data.items() if not k.startswith("__")}
        if not entries:
            print(f"No entries for type '{entry_type}'.")
            return pd.DataFrame()

        df = pd.DataFrame.from_dict(entries, orient="index")
        df.index.name = "entry_id"
        df.reset_index(inplace=True)

        if raw:
            cols_order = ["entry_id", "entity_id", "timestamp", "description", "raw_csv_path", "processed_files"]
            other_cols = [c for c in df.columns if c not in cols_order]
            return df[[c for c in cols_order if c in df.columns] + other_cols]

        return self._format_entries_dataframe(df, include_paths=include_paths)

    def _format_entries_dataframe(self, df: pd.DataFrame, include_paths: bool = False) -> pd.DataFrame:
        if df.empty:
            return df

        def _to_dict(val):
            if val is None or pd.isna(val):
                return {}
            if isinstance(val, dict):
                return val
            if isinstance(val, str):
                s = val.strip()
                if not s or s == "{}" or s.lower() == "nan":
                    return {}
                try:
                    res = ast.literal_eval(s)
                    if isinstance(res, dict):
                        return res
                except Exception:
                    pass
            return {}

        res = df.copy()
        base_priority = ["entry_id", "entity_id", "timestamp", "description"]
        base_cols = [c for c in base_priority if c in res.columns]

        raw_paths = res.get("raw_csv_path", pd.Series(index=res.index, dtype=object))
        proc_files = res.get("processed_files", pd.Series(index=res.index, dtype=object)).apply(_to_dict)
        rel_files = res.get("related_files", pd.Series(index=res.index, dtype=object)).apply(_to_dict)
        proc_meta = res.get("processed_metadata", pd.Series(index=res.index, dtype=object)).apply(_to_dict)

        file_cols = {}

        # 1. Raw file columns
        has_raw = raw_paths.apply(lambda p: bool(p and not pd.isna(p) and str(p).strip()))
        file_cols["raw_file_available"] = has_raw.map({True: "Available", False: "Not Available"})
        if include_paths:
            file_cols["raw_file_path"] = raw_paths.apply(
                lambda p: str(p) if (p and not pd.isna(p) and str(p).strip()) else None
            )

        # 2. Processed files columns (sub-columns per populated tag)
        all_proc_tags = sorted(list({tag for d in proc_files for tag in d.keys()}))
        for tag in all_proc_tags:
            avail_col = f"proc_{tag}_available"
            file_cols[avail_col] = proc_files.apply(
                lambda d: "Available" if tag in d else "Not Available"
            )

            # Extract comment/metadata if available, placed next to availability
            def _extract_meta_comment(meta_dict, t=tag):
                m = meta_dict.get(t, {})
                if isinstance(m, dict):
                    comment = m.get("comment")
                    if comment:
                        return str(comment)
                    other_items = [f"{k}: {v}" for k, v in m.items() if v]
                    return " | ".join(other_items) if other_items else None
                elif isinstance(m, str) and m.strip():
                    return m.strip()
                return None

            comment_series = proc_meta.apply(_extract_meta_comment)
            if any(c is not None for c in comment_series):
                comment_col = f"proc_{tag}_comment"
                file_cols[comment_col] = comment_series

            if include_paths:
                path_col = f"proc_{tag}_path"
                file_cols[path_col] = proc_files.apply(
                    lambda d: str(d[tag]) if tag in d else None
                )

        # 3. Related files columns (sub-columns per populated label)
        all_rel_labels = sorted(list({lbl for d in rel_files for lbl in d.keys()}))
        for lbl in all_rel_labels:
            avail_col = f"rel_{lbl}_available"
            file_cols[avail_col] = rel_files.apply(
                lambda d: "Available" if lbl in d else "Not Available"
            )
            if include_paths:
                path_col = f"rel_{lbl}_path"
                file_cols[path_col] = rel_files.apply(
                    lambda d: str(d[lbl]) if lbl in d else None
                )

        # Drop old nested/unformatted columns
        cols_to_drop = ["raw_csv_path", "processed_files", "related_files", "processed_metadata"]
        res = res.drop(columns=cols_to_drop, errors="ignore")

        # Organize final columns logically
        file_df = pd.DataFrame(file_cols, index=res.index)
        other_meta = [c for c in res.columns if c not in base_cols]
        general_order = ["date", "time", "weight_kg", "notes"]
        gen_cols = [c for c in general_order if c in other_meta]
        remaining = [c for c in other_meta if c not in gen_cols]

        final_df = pd.concat([res[base_cols + gen_cols], file_df, res[remaining]], axis=1)
        return final_df


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
        self._safe_makedirs(proc_save_dir)
        filename = self._build_processed_filename(entry_id, tag)
        full_path = f"{proc_save_dir}/{filename}"
        rel_path = self._rel_path(full_path)

        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp:
            tmp_path = tmp.name
        try:
            df.to_parquet(tmp_path,engine='fastparquet', index=False)
            self.fs.put(tmp_path, full_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

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

        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as tmp:
            tmp_path = tmp.name
        try:
            df.to_parquet(tmp_path,engine='fastparquet', index=False)
            self.fs.put(tmp_path, old_full_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
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
