import os
import json
import fsspec
from datetime import datetime, timezone
from typing import Dict, Optional, Union, Any


def format_bytes(size_bytes: int, unit: str = "auto") -> str:
    """Format a byte size into a human-readable string.

    Args:
        size_bytes (int): Size in bytes.
        unit (str, optional): Target unit ('auto', 'B', 'KB', 'MB', 'GB', 'TB', 'PB'). Defaults to 'auto'.

    Returns:
        str: Formatted size string.
    """
    if size_bytes < 0:
        size_bytes = 0

    unit_clean = unit.strip().upper() if unit else "AUTO"
    if unit_clean == "B":
        return f"{size_bytes} B"
    elif unit_clean == "KB":
        return f"{size_bytes / 1024:.2f} KB"
    elif unit_clean == "MB":
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    elif unit_clean == "GB":
        return f"{size_bytes / (1024 ** 3):.2f} GB"
    elif unit_clean == "TB":
        return f"{size_bytes / (1024 ** 4):.2f} TB"
    elif unit_clean == "PB":
        return f"{size_bytes / (1024 ** 5):.2f} PB"

    # Auto scaling
    n = float(size_bytes)
    for u in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(n) < 1024.0:
            return f"{int(n)} B" if u == "B" else f"{n:.2f} {u}"
        n /= 1024.0
    return f"{n:.2f} EB"


try:
    from gdrive_fsspec.core import GoogleDriveFileSystem
    _original_kw = GoogleDriveFileSystem._drive_kw
    def _patched_kw(self):
        kw = _original_kw(self)
        kw["supportsAllDrives"] = True
        kw["includeItemsFromAllDrives"] = True
        return kw
    GoogleDriveFileSystem._drive_kw = _patched_kw
except ImportError:
    pass


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
        """
        Initializes the Dataset Store.

        Args:
            base_dir (str): The root directory for the dataset store (e.g., 'path/to/dataset', 'gdrive://MyDataset').
            backend (str, optional): The storage backend to use. Options are 'local' or 'gdrive'. Defaults to 'local'.
            entry_id_format (str, optional): The format string for generating entry IDs. Defaults to "{type}_{num:06d}".
            entity_id_format (str, optional): The format string for generating entity IDs. Defaults to "ent_{num:04d}".
            raw_filename_format (str, optional): The format string for naming raw data files. Defaults to "{entry_id}_{entity_id}_{ts}_{original}".
            processed_filename_format (str, optional): The format string for naming processed data files. Defaults to "{entry_id}_{tag}.parquet".
            **fsspec_kwargs: Additional keyword arguments passed to the underlying fsspec filesystem (e.g., authentication kwargs).
        """
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
            self._safe_makedirs(self.base_dir)

        
        self._safe_makedirs(self.index_dir)
        self._safe_makedirs(self.raw_dir)
        self._safe_makedirs(self.processed_dir)

        print(f"Store initialised at: {self.base_dir} (Backend: {self.backend})")

    def _safe_makedirs(self, path: str) -> None:
        """makedirs wrapper that handles gdrive_fsspec not respecting exist_ok."""
        try:
            self.fs.makedirs(path, exist_ok=True)
        except FileExistsError:
            pass

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
        self, entry_id: str, entity_id: Optional[str], timestamp: str, original_name: str
    ) -> str:
        e_id = entity_id if entity_id is not None else "none"
        return self.raw_filename_format_str.format(
            entry_id=entry_id,
            entity_id=e_id,
            ts=timestamp,
            original=original_name,
        )

    def _build_processed_filename(self, entry_id: str, tag: str) -> str:
        return self.processed_filename_format_str.format(
            entry_id=entry_id, tag=tag
        )

    def _normalize_rel_path(self, full_path: str) -> str:
        """Normalizes a full path to a path relative to self.base_dir."""
        if not full_path:
            return ""

        path_str = str(full_path).replace("\\", "/")
        base_str = str(self.base_dir).replace("\\", "/") if self.base_dir else ""

        if self.backend == "local":
            try:
                abs_base = os.path.abspath(self.base_dir) if self.base_dir else os.getcwd()
                abs_path = os.path.abspath(full_path)
                rel = os.path.relpath(abs_path, abs_base).replace("\\", "/")
                if not rel.startswith(".."):
                    return rel
            except Exception:
                pass

        if base_str:
            if path_str.startswith(base_str + "/"):
                return path_str[len(base_str) + 1:]
            elif path_str.startswith(base_str):
                return path_str[len(base_str):].lstrip("/")

        return path_str.lstrip("/")

    def storage_summary(
        self,
        by_folder: bool = False,
        depth: Optional[Union[int, str]] = None,
        by_file_type: bool = False,
        print_summary: bool = True,
        unit: str = "auto",
        path: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Provides a storage size and file count summary of the dataset store.

        Parameters:
            by_folder (bool, optional): If True, groups storage and file counts by folder.
                Defaults to False. Automatically enabled if depth is provided.
            depth (int or str, optional): Controls the number of subfolder levels to group by.
                - None or 'all': Summarizes by all subfolder levels.
                - int (e.g., 1, 2, 3): Limits grouping to the specified subfolder depth.
            by_file_type (bool, optional): If True, breaks down storage by file extension/type.
                Defaults to False. Also accepts alias by_extension=True or by_type=True.
            print_summary (bool, optional): If True, prints a formatted summary to stdout.
                Defaults to True.
            unit (str, optional): Unit for formatted sizes ('auto', 'B', 'KB', 'MB', 'GB', 'TB').
                Defaults to 'auto'.
            path (str, optional): Specific subpath within store to summarize. Defaults to store root.
            **kwargs: Extra options such as max_depth, folder_depth, as_df.

        Returns:
            dict or pandas.DataFrame: Summary dictionary containing total size and breakdown details,
            or a pandas.DataFrame if as_df=True.
        """
        # Resolve depth aliases
        if depth is None:
            depth = kwargs.get("max_depth", kwargs.get("folder_depth", kwargs.get("levels", None)))

        if isinstance(depth, str):
            if depth.strip().lower() in ("all", "none", "*"):
                depth = None
            else:
                try:
                    depth = int(depth)
                except ValueError:
                    depth = None

        if depth is not None and isinstance(depth, int) and depth < 0:
            depth = None

        # Auto-enable by_folder if depth is explicitly provided
        if not by_folder and depth is not None:
            by_folder = True

        # Resolve by_file_type aliases
        if not by_file_type:
            by_file_type = kwargs.get("by_type", kwargs.get("by_extension", False))

        # Determine target directory
        if path:
            target_dir = self._full_path(path)
        else:
            target_dir = self.base_dir if self.base_dir else ""

        file_entries = []

        if not target_dir or self.fs.exists(target_dir):
            found = None
            try:
                found = self.fs.find(target_dir, detail=True)
            except Exception:
                try:
                    found_names = self.fs.find(target_dir, detail=False)
                    found = {name: self.fs.info(name) for name in found_names}
                except Exception:
                    found = {}
                    try:
                        for root, dirs, files in self.fs.walk(target_dir, detail=True):
                            for name, info in files.items():
                                found[name] = info
                    except Exception:
                        pass

            if isinstance(found, list):
                dict_found = {}
                for item in found:
                    if isinstance(item, dict):
                        dict_found[item.get("name", "")] = item
                    elif isinstance(item, str):
                        try:
                            dict_found[item] = self.fs.info(item)
                        except Exception:
                            dict_found[item] = {"name": item, "size": 0, "type": "file"}
                found = dict_found

            if isinstance(found, dict):
                for full_path, info in found.items():
                    if isinstance(info, dict):
                        if info.get("type") == "directory":
                            continue
                        size = info.get("size")
                        if size is None:
                            size = info.get("file_size", info.get("bytes", None))
                    else:
                        size = None

                    if (size is None or size < 0) and hasattr(self.fs, "size"):
                        try:
                            size = self.fs.size(full_path)
                        except Exception:
                            size = 0
                    elif size is None or size < 0:
                        size = 0

                    try:
                        size_int = int(size)
                    except (ValueError, TypeError):
                        size_int = 0

                    rel_path = self._normalize_rel_path(full_path)
                    if not rel_path or rel_path == ".":
                        continue

                    file_entries.append((rel_path, size_int))

        total_files = len(file_entries)
        total_size_bytes = sum(size for _, size in file_entries)
        total_size_formatted = format_bytes(total_size_bytes, unit=unit)

        summary_data: Dict[str, Any] = {
            "store_base_dir": self.base_dir,
            "backend": self.backend,
            "total_size_bytes": total_size_bytes,
            "total_size_formatted": total_size_formatted,
            "total_files": total_files,
        }

        if by_folder:
            folder_stats: Dict[str, Dict[str, Any]] = {}
            for rel_path, size in file_entries:
                dir_name = os.path.dirname(rel_path).replace("\\", "/").strip("/")
                parts = [p for p in dir_name.split("/") if p and p != "."]
                if not parts:
                    folder_key = "."
                elif depth is not None and depth > 0:
                    folder_key = "/".join(parts[:depth])
                else:
                    folder_key = "/".join(parts)

                if folder_key not in folder_stats:
                    folder_stats[folder_key] = {
                        "size_bytes": 0,
                        "file_count": 0,
                        "level": len(parts[:depth]) if depth is not None and depth > 0 else len(parts),
                    }
                folder_stats[folder_key]["size_bytes"] += size
                folder_stats[folder_key]["file_count"] += 1

            for folder_key, stats in folder_stats.items():
                pct = round((stats["size_bytes"] / total_size_bytes * 100), 2) if total_size_bytes > 0 else 0.0
                stats["size_formatted"] = format_bytes(stats["size_bytes"], unit=unit)
                stats["percentage"] = pct

            sorted_folders = dict(sorted(folder_stats.items(), key=lambda item: (-item[1]["size_bytes"], item[0])))
            summary_data["by_folder"] = sorted_folders

        if by_file_type:
            type_stats: Dict[str, Dict[str, Any]] = {}
            for rel_path, size in file_entries:
                filename = os.path.basename(rel_path)
                ext = os.path.splitext(filename)[1].lower()
                if not ext:
                    if filename.startswith("."):
                        ext = filename.lower()
                    else:
                        ext = "(no extension)"

                if ext not in type_stats:
                    type_stats[ext] = {
                        "size_bytes": 0,
                        "file_count": 0,
                    }
                type_stats[ext]["size_bytes"] += size
                type_stats[ext]["file_count"] += 1

            for ext, stats in type_stats.items():
                pct = round((stats["size_bytes"] / total_size_bytes * 100), 2) if total_size_bytes > 0 else 0.0
                stats["size_formatted"] = format_bytes(stats["size_bytes"], unit=unit)
                stats["percentage"] = pct

            sorted_types = dict(sorted(type_stats.items(), key=lambda item: (-item[1]["size_bytes"], item[0])))
            summary_data["by_file_type"] = sorted_types

        if print_summary:
            sep_len = 65
            print(f"💾 Storage Summary")
            print(f"{'='*sep_len}")
            print(f"Base Directory : {summary_data['store_base_dir']}")
            print(f"Backend        : {summary_data['backend']}")
            print(f"Total Storage  : {summary_data['total_size_formatted']} ({summary_data['total_size_bytes']:,} bytes)")
            print(f"Total Files    : {summary_data['total_files']:,}")

            if by_folder:
                depth_label = f"{depth}" if depth is not None else "all"
                print(f"{'-'*sep_len}")
                print(f"📁 Folder Breakdown (Depth: {depth_label})")
                print(f"{'-'*sep_len}")
                if not summary_data.get("by_folder"):
                    print("  (No files found)")
                else:
                    folder_keys = list(summary_data["by_folder"].keys())
                    max_len = max(len(k if k != "." else ". (root)") for k in folder_keys) if folder_keys else 10
                    col_w = max(max_len + 2, 28)
                    total_w = max(col_w + 35, sep_len)
                    print(f"{'Folder':<{col_w}} {'Size':>12} {'Files':>8} {'% Store':>10}")
                    print(f"{'-'*total_w}")
                    for folder, f_stats in summary_data["by_folder"].items():
                        display_folder = folder if folder != "." else ". (root)"
                        pct_str = f"{f_stats['percentage']:.1f}%"
                        print(f"{display_folder:<{col_w}} {f_stats['size_formatted']:>12} {f_stats['file_count']:>8} {pct_str:>10}")

            if by_file_type:
                print(f"{'-'*sep_len}")
                print(f"📄 File Type Breakdown")
                print(f"{'-'*sep_len}")
                if not summary_data.get("by_file_type"):
                    print("  (No files found)")
                else:
                    type_keys = list(summary_data["by_file_type"].keys())
                    max_len = max(len(k) for k in type_keys) if type_keys else 10
                    col_w = max(max_len + 2, 28)
                    total_w = max(col_w + 35, sep_len)
                    print(f"{'File Type':<{col_w}} {'Size':>12} {'Files':>8} {'% Store':>10}")
                    print(f"{'-'*total_w}")
                    for ext, t_stats in summary_data["by_file_type"].items():
                        pct_str = f"{t_stats['percentage']:.1f}%"
                        print(f"{ext:<{col_w}} {t_stats['size_formatted']:>12} {t_stats['file_count']:>8} {pct_str:>10}")

            print(f"{'='*sep_len}")

        if kwargs.get("as_df", False):
            import pandas as pd
            if by_folder and not by_file_type:
                return pd.DataFrame([
                    {
                        "folder": k,
                        "size_bytes": v["size_bytes"],
                        "size_formatted": v["size_formatted"],
                        "file_count": v["file_count"],
                        "percentage": v["percentage"],
                        "level": v["level"],
                    }
                    for k, v in summary_data["by_folder"].items()
                ])
            elif by_file_type and not by_folder:
                return pd.DataFrame([
                    {
                        "file_type": k,
                        "size_bytes": v["size_bytes"],
                        "size_formatted": v["size_formatted"],
                        "file_count": v["file_count"],
                        "percentage": v["percentage"],
                    }
                    for k, v in summary_data["by_file_type"].items()
                ])
            elif by_folder and by_file_type:
                df_folders = pd.DataFrame([
                    {
                        "folder": k,
                        "size_bytes": v["size_bytes"],
                        "size_formatted": v["size_formatted"],
                        "file_count": v["file_count"],
                        "percentage": v["percentage"],
                        "level": v["level"],
                    }
                    for k, v in summary_data["by_folder"].items()
                ])
                df_types = pd.DataFrame([
                    {
                        "file_type": k,
                        "size_bytes": v["size_bytes"],
                        "size_formatted": v["size_formatted"],
                        "file_count": v["file_count"],
                        "percentage": v["percentage"],
                    }
                    for k, v in summary_data["by_file_type"].items()
                ])
                return {"folders": df_folders, "file_types": df_types}
            else:
                return pd.DataFrame([{
                    "store_base_dir": summary_data["store_base_dir"],
                    "backend": summary_data["backend"],
                    "total_size_bytes": summary_data["total_size_bytes"],
                    "total_size_formatted": summary_data["total_size_formatted"],
                    "total_files": summary_data["total_files"],
                }])

        return summary_data

    file_size_summary = storage_summary
    get_storage_summary = storage_summary
