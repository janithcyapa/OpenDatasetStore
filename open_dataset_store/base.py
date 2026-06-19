import json
import fsspec
from datetime import datetime, timezone
from typing import Dict

class BaseOpenDatasetStore:
    def __init__(
        self,
        base_dir: str,
        backend: str = "local",
        entry_id_format: str = "{type}_{num:06d}",
        entity_id_format: str = "ent_{num:04d}",
        raw_filename_format: str = "{entry_id}_{entity_id}_{ts}_{original}",
        processed_filename_format: str = "{entry_id}_{tag}.parquet",
        **fsspec_kwargs,
    ):
        self.backend = backend
        self.entry_id_format_str = entry_id_format
        self.entity_id_format_str = entity_id_format
        self.raw_filename_format_str = raw_filename_format
        self.processed_filename_format_str = processed_filename_format

        if self.backend == "gdrive":
            self.base_dir = base_dir.replace("gdrive://", "").rstrip('/')
            self.fs = fsspec.filesystem("gdrive", **fsspec_kwargs)
        else:
            self.base_dir = base_dir.replace("file://", "").rstrip('/')
            self.fs = fsspec.filesystem("file", **fsspec_kwargs)

        if self.base_dir:
            self.index_dir = f"{self.base_dir}/index"
            self.raw_dir = f"{self.base_dir}/raw_data"
            self.processed_dir = f"{self.base_dir}/processed_data"
        else:
            self.index_dir = "index"
            self.raw_dir = "raw_data"
            self.processed_dir = "processed_data"

        # ensure directory structure exists
        if self.base_dir:
            self.fs.makedirs(self.base_dir, exist_ok=True)

        
        self.fs.makedirs(self.index_dir, exist_ok=True)
        self.fs.makedirs(self.raw_dir, exist_ok=True)
        self.fs.makedirs(self.processed_dir, exist_ok=True)

        print(f"Store initialised at: {self.base_dir} (Backend: {self.backend})")

    def _full_path(self, rel_path: str) -> str:
        return f"{self.base_dir}/{rel_path}" if self.base_dir else rel_path

    def _rel_path(self, full_path: str) -> str:
        return full_path.replace(self.base_dir + "/", "", 1) if self.base_dir else full_path

    def _get_entity_index_path(self, entity_type: str) -> str:
        return f"{self.index_dir}/entities_{entity_type}.json"

    def _get_entry_index_path(self, entry_type: str) -> str:
        return f"{self.index_dir}/entries_{entry_type}.json"

    def _load_json(self, path: str) -> Dict:
        if self.fs.exists(path):
            with self.fs.open(path, "r") as f:
                return json.load(f)
        return {}

    def _save_json(self, path: str, data: Dict) -> None:
        with self.fs.open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _generate_timestamp(self) -> str:
        return str(int(datetime.now(timezone.utc).timestamp()))

    def _generate_entry_id(self, entry_type: str, index: Dict) -> str:
        counter = index.get("__auto_counter__", 0)
        new_counter = counter + 1
        index["__auto_counter__"] = new_counter
        return self.entry_id_format_str.format(type=entry_type, num=new_counter)

    def _generate_entity_id(self, entity_type: str, index: Dict) -> str:
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
