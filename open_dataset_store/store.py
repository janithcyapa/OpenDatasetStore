from .base import BaseOpenDatasetStore
from .mixins.entity_mixin import EntityManagementMixin
from .mixins.entry_mixin import EntryManagementMixin
from .mixins.related_files_mixin import RelatedFilesMixin

class OpenDatasetStore(
    EntityManagementMixin,
    EntryManagementMixin,
    RelatedFilesMixin,
    BaseOpenDatasetStore,
):
    """Main class managing the dataset store on Google Drive."""
    pass

def quick_start(base_dir: str, backend: str = "local") -> OpenDatasetStore:
    """Create a store instance with sensible defaults.

    Example:
        store = quick_start('/content/drive/MyDrive/MyResearch', backend='local')
        # OR 
        store = quick_start('gdrive://MyResearch', backend='gdrive')
    """
    return OpenDatasetStore(
        base_dir=base_dir,
        backend=backend,
        entry_id_format="entry_{num:04d}",
        entity_id_format="entity_{num:04d}",
        raw_filename_format="{entry_id}_{entity_id}_{ts}_{original}",
        processed_filename_format="{entry_id}_{tag}.parquet",
    )
