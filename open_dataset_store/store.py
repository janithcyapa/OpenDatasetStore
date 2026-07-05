from typing import Dict, Any
from .base import BaseOpenDatasetStore
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
    
    def summary(self, print_summary: bool = True) -> Dict[str, Any]:
        """Provides a summary of the dataset store including entity and entry counts."""
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
