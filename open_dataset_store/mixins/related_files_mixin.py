import os
from typing import Optional

try:
    # pyrefly: ignore [missing-import]
    from google.colab import files as colab_files
    IN_COLAB = True
except ImportError:
    IN_COLAB = False

class RelatedFilesMixin:
    def add_related_file(self, entry_type: str, entry_id: str, label: str, local_path: str) -> str:
        idx_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(idx_path)
        if entry_id not in index_data:
            raise KeyError(f"Entry {entry_id} not found.")
        
        entity_id = index_data[entry_id].get("entity_id", "unknown")

        ext = os.path.splitext(local_path)[1]
        file_dir = f"{self.base_dir}/related_files/{entry_type}/{entry_id}"
        self.fs.makedirs(file_dir, exist_ok=True)
        
        dest_filename = f"{entry_id}_{entity_id}_{label}{ext}"
        dest_path = f"{file_dir}/{dest_filename}"
        rel_path = dest_path.replace(self.base_dir + "/", "", 1)

        self.fs.put(local_path, dest_path)

        index_data[entry_id].setdefault("related_files", {})[label] = rel_path
        self._save_json(idx_path, index_data)
        
        print(f"📎 Attached: {dest_filename}")
        return rel_path

    def upload_related_file_interactive(self, entry_type: str, entry_id: str, label: str) -> Optional[str]:
        if IN_COLAB:
            print(f"📤 Select file for '{label}' (Entry: {entry_id})...")
            uploaded = colab_files.upload()
            if not uploaded:
                print("🚫 Upload cancelled.")
                return None
            temp_filename = list(uploaded.keys())[0]
            try:
                rel_path = self.add_related_file(entry_type, entry_id, label, temp_filename)
                return rel_path
            finally:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
        else:
            local_path = input(f"📤 Enter local file path for '{label}' (Entry: {entry_id}): ").strip()
            if not os.path.exists(local_path):
                print("🚫 File not found.")
                return None
            return self.add_related_file(entry_type, entry_id, label, local_path)
                
    def download_related_file(self, entry_type: str, entry_id: str, label: str, dest_folder: str = "/content/" if IN_COLAB else ".") -> str:
        meta = self.get_entry(entry_type, entry_id)
        related = meta.get("related_files", {})
        
        if label not in related:
            raise KeyError(f"No related file with label '{label}' found for {entry_id}.")
        
        drive_path = f"{self.base_dir}/{related[label]}"
        local_path = os.path.join(dest_folder, related[label].split("/")[-1])
        
        if not self.fs.exists(drive_path):
            raise FileNotFoundError(f"File missing on Drive: {drive_path}")
            
        self.fs.get(drive_path, local_path)
        print(f"📥 Downloaded to: {local_path}")
        return local_path

    def delete_related_file(self, entry_type: str, entry_id: str, label: str) -> None:
        idx_path = self._get_entry_index_path(entry_type)
        index_data = self._load_json(idx_path)
        
        if entry_id not in index_data or label not in index_data[entry_id].get("related_files", {}):
            print(f"⚠️ Label '{label}' not found for {entry_id}. Skipping.")
            return

        rel_path = index_data[entry_id]["related_files"][label]
        full_path = f"{self.base_dir}/{rel_path}"

        if self.fs.exists(full_path):
            self.fs.rm(full_path)
            print(f"🗑️ Deleted file from Drive: {rel_path}")

        del index_data[entry_id]["related_files"][label]
        self._save_json(idx_path, index_data)
        print(f"✅ Removed '{label}' from {entry_id} index.")

    def update_related_file(self, entry_type: str, entry_id: str, label: str, local_path: str) -> str:
        self.delete_related_file(entry_type, entry_id, label)
        return self.add_related_file(entry_type, entry_id, label, local_path)
