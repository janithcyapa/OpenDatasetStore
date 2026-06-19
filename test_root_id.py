import fsspec
# Create a test folder normally to get its ID
fs = fsspec.filesystem("gdrive")
fs.makedirs("TestRootFolder123", exist_ok=True)
folder_id = fs.info("TestRootFolder123")["id"]
print(f"Created folder with ID: {folder_id}")

# Now instantiate a new FS with that ID as root
fs2 = fsspec.filesystem("gdrive", root_file_id=folder_id)
# Try creating something inside it
try:
    fs2.makedirs("index", exist_ok=True)
    print("Successfully created 'index' inside the folder by ID!")
    print("LS:", fs2.ls(""))
except Exception as e:
    print("Error:", e)
