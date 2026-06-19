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
