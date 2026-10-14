from typing import Dict, Any, Optional, Union
from .base import BaseOpenDatasetStore, format_bytes
from .mixins.entity_mixin import EntityManagementMixin
from .mixins.entry_mixin import EntryManagementMixin
from .mixins.related_files_mixin import RelatedFilesMixin
from .mixins.data_inspector_mixin import DataInspectorMixin
import open_dataset_store.plotting # Initializes global plotly settings

class OpenDatasetStore(
    EntityManagementMixin,
    EntryManagementMixin,
    RelatedFilesMixin,
    DataInspectorMixin,
    BaseOpenDatasetStore,
):
    """
    Main class managing the dataset store.

    This class provides the primary interface for managing entities, entries, and their related files.
    It combines functionalities from EntityManagementMixin, EntryManagementMixin, RelatedFilesMixin, 
    and BaseOpenDatasetStore.

    Initialization:
        While you can instantiate this class directly via its constructor inherited from BaseOpenDatasetStore,
        it is often easier to use the `quick_start` function for typical local or Google Drive setups.

        When initializing directly:
        >>> store = OpenDatasetStore(
        ...     base_dir='/path/to/dataset',
        ...     backend='local',
        ... )
        
        Or for Google Drive:
        >>> store = OpenDatasetStore(
        ...     base_dir='gdrive://MyDataset',
        ...     backend='gdrive',
        ... )
    """
    
    def summary(
        self,
        print_summary: bool = True,
        include_storage: bool = False,
        **storage_kwargs,
    ) -> Dict[str, Any]:
        """Provides a summary of the dataset store including entity and entry counts, and optionally storage stats."""
        summary_data = {
            "store_base_dir": self.base_dir,
            "backend": self.backend,
            "entities": {},
            "entries": {},
            "total_entities": 0,
            "total_entries": 0,
        }

        if self.fs.exists(self.index_dir):
            try:
                index_files = self.fs.ls(self.index_dir)
            except Exception:
                index_files = []

            for file_path in index_files:
                if isinstance(file_path, dict):
                    file_path = file_path.get("name", "")
                
                basename = str(file_path).split("/")[-1].split("\\")[-1]
                if basename.startswith("entities_") and basename.endswith(".json"):
                    entity_type = basename[len("entities_"):-len(".json")]
                    data = self._load_json(self._get_entity_index_path(entity_type))
                    count = sum(1 for k in data.keys() if not str(k).startswith("__"))
                    summary_data["entities"][entity_type] = count
                    summary_data["total_entities"] += count
                elif basename.startswith("entries_") and basename.endswith(".json"):
                    entry_type = basename[len("entries_"):-len(".json")]
                    data = self._load_json(self._get_entry_index_path(entry_type))
                    count = sum(1 for k in data.keys() if not str(k).startswith("__"))
                    summary_data["entries"][entry_type] = count
                    summary_data["total_entries"] += count

        if include_storage:
            storage_stats = self.storage_summary(print_summary=False, **storage_kwargs)
            summary_data["storage"] = storage_stats

        if print_summary:
            print(f"📊 Dataset Store Summary")
            print(f"{'='*30}")
            print(f"Base Directory : {summary_data['store_base_dir']}")
            print(f"Backend        : {summary_data['backend']}")
            print(f"{'-'*30}")
            print(f"Entities (Total: {summary_data['total_entities']})")
            if not summary_data["entities"]:
                print("  (None)")
            for e_type, count in summary_data["entities"].items():
                print(f"  - {e_type}: {count}")
            print(f"{'-'*30}")
            print(f"Entries (Total: {summary_data['total_entries']})")
            if not summary_data["entries"]:
                print("  (None)")
            for e_type, count in summary_data["entries"].items():
                print(f"  - {e_type}: {count}")

            if include_storage and "storage" in summary_data:
                st = summary_data["storage"]
                print(f"{'-'*30}")
                print(f"Storage (Total: {st['total_size_formatted']})")
                print(f"  - Total Files: {st['total_files']:,}")
                print(f"  - Total Bytes: {st['total_size_bytes']:,}")
                if "by_folder" in st and st["by_folder"]:
                    print("  - Folders:")
                    for f_name, f_info in st["by_folder"].items():
                        disp_f = f_name if f_name != "." else ". (root)"
                        print(f"    * {disp_f}: {f_info['size_formatted']} ({f_info['file_count']} files)")
                if "by_file_type" in st and st["by_file_type"]:
                    print("  - File Types:")
                    for t_name, t_info in st["by_file_type"].items():
                        print(f"    * {t_name}: {t_info['size_formatted']} ({t_info['file_count']} files)")

            print(f"{'='*30}")

        return summary_data

def quick_start(base_dir: str, backend: str = "local", **kwargs) -> OpenDatasetStore:
    """Create a store instance with sensible defaults.

    Example:
        store = quick_start('/content/drive/MyDrive/MyResearch', backend='local')
        # OR 
        store = quick_start('gdrive://MyResearch', backend='gdrive')
        # Shared Folder:
        store = quick_start('gdrive://', backend='gdrive', root_file_id='1Gqd9XGcwvtkWpsygrdWPvjLr5cuYmyNr')
    """
    return OpenDatasetStore(
        base_dir=base_dir,
        backend=backend,
        entry_id_format="entry_{num:04d}",
        entity_id_format="entity_{num:04d}",
        raw_filename_format="{entry_id}_{entity_id}_{ts}_{original}",
        processed_filename_format="{entry_id}_{tag}.parquet",
        **kwargs,
    )


def storage_summary(
    store_or_path: Any,
    by_folder: bool = False,
    depth: Optional[Union[int, str]] = None,
    by_file_type: bool = False,
    print_summary: bool = True,
    unit: str = "auto",
    backend: str = "local",
    **kwargs,
) -> Any:
    """
    Summarize dataset store storage size and file counts.

    Can be invoked directly on an existing OpenDatasetStore instance or a directory path.

    Parameters:
        store_or_path: An OpenDatasetStore instance or a directory path string.
        by_folder (bool, optional): If True, breaks down storage by folder.
        depth (int or str, optional): Subfolder depth to group by (e.g. 1, 2, 'all', None).
        by_file_type (bool, optional): If True, breaks down storage by file type.
        print_summary (bool, optional): If True, prints a formatted summary.
        unit (str, optional): Target size unit ('auto', 'B', 'KB', 'MB', 'GB', 'TB').
        backend (str, optional): Storage backend if a path is provided ('local' or 'gdrive').
        **kwargs: Additional options such as max_depth, folder_depth, as_df.

    Returns:
        dict or pandas.DataFrame: Storage summary data.
    """
    if hasattr(store_or_path, "storage_summary"):
        return store_or_path.storage_summary(
            by_folder=by_folder,
            depth=depth,
            by_file_type=by_file_type,
            print_summary=print_summary,
            unit=unit,
            **kwargs,
        )

    store = quick_start(base_dir=str(store_or_path), backend=backend)
    return store.storage_summary(
        by_folder=by_folder,
        depth=depth,
        by_file_type=by_file_type,
        print_summary=print_summary,
        unit=unit,
        **kwargs,
    )


file_size_summary = storage_summary
