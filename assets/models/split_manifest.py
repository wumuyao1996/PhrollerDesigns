import json
import os

manifest_path = "manifest.json"
out_dir = "json"

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

with open(manifest_path, 'r') as f:
    data = json.load(f)

new_manifest = []

for item in data:
    # Get the file name
    file_name = item.get("file")
    if not file_name:
        # fallback if file name doesn't exist
        file_name = f"{item['id']}.json"
        item["file"] = file_name
    
    # Save individual JSON
    with open(os.path.join(out_dir, file_name), 'w') as out_f:
        json.dump(item, out_f, indent=2)
    
    # Add minimal entry to new manifest
    # keep id, label, file, tags
    minimal_item = {
        "id": item["id"],
        "label": item.get("label"),
        "file": file_name,
    }
    if "tags" in item:
        minimal_item["tags"] = item["tags"]
        
    new_manifest.append(minimal_item)

# Write back the minimal manifest
with open(manifest_path, 'w') as f:
    json.dump(new_manifest, f, indent=2)

print(f"Processed {len(data)} items.")
