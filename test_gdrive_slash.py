import fsspec
fs = fsspec.filesystem("gdrive", root_file_id="1nDQy9xK7MFG-aRY7TIt2xqgZ-i9UKl3F")
try:
    fs.makedirs("index", exist_ok=True)
    print("Makedirs 'index' worked!")
    fs.makedirs("/raw_data", exist_ok=True)
    print("Makedirs '/raw_data' worked!")
except Exception as e:
    print("Error:", type(e), e)
