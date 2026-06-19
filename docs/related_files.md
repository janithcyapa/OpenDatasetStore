# Related Files Management

Sometimes you have large binary files (like videos, images, or archives) that belong to an entry but aren't tabular data.

### Add a File
```python
rel_path = store.add_related_file(
    entry_type="experiments", 
    entry_id="exp_001", 
    label="front_camera_video", 
    local_path="./videos/trial1.mp4"
)
```
This copies the file to the dataset store (or uploads it via `fsspec` if using the `gdrive` backend).

### Download a File
```python
local_path = store.download_related_file(
    entry_type="experiments", 
    entry_id="exp_001", 
    label="front_camera_video",
    dest_folder="./temp"
)
```
Because video libraries usually require a real file path, this method explicitly downloads the remote file to your local disk.

### Interactive Upload
```python
store.upload_related_file_interactive("experiments", "exp_001", "front_camera_video")
```
Functions identically to interactive entry uploads (Colab widget or terminal prompt).
