#!/bin/bash

# Configuration - Ensure these match your Phase 2 setup
DESIGNS_DIR="assets/designs"
MANIFEST_PATH="assets/manifest.json"

# Check if we are in a git repository
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: Not in a git repository. Please run this inside your flutter-designs folder."
    exit 1
fi

# Check if the user passed "delete" as an argument
if [[ "$1" == "delete" ]]; then
    # --- DELETE MODE ---
    echo "--- Delete Design Mode ---"
    if [[ ! -f "$MANIFEST_PATH" ]]; then
        echo "Error: Manifest file not found."
        exit 1
    fi

    echo "Current designs in manifest:"
    # Simple grep to show filenames from the manifest
    grep '"file":' "$MANIFEST_PATH" | cut -d'"' -f4
    
    read -p "Enter the exact filename to delete (e.g., modern_dark.json): " DELETE_NAME
    
    if [[ -z "$DELETE_NAME" ]]; then
        echo "Operation cancelled."
        exit 0
    fi

    # Remove the file
    if [[ -f "$DESIGNS_DIR/$DELETE_NAME" ]]; then
        rm "$DESIGNS_DIR/$DELETE_NAME"
        echo "✅ Deleted file: $DESIGNS_DIR/$DELETE_NAME"
    else
        echo "Warning: File $DELETE_NAME not found in designs directory, cleaning manifest only."
    fi

    # Remove the entry from the manifest.json via Python
    python3 -c "
import json, sys
try:
    with open('$MANIFEST_PATH', 'r') as f:
        data = json.load(f)
    new_data = [item for item in data if item.get('file') != '$DELETE_NAME']
    with open('$MANIFEST_PATH', 'w') as f:
        json.dump(new_data, f, indent=2)
    print('✅ Updated $MANIFEST_PATH')
except Exception as e:
    print(f'Error updating manifest: {e}')
"
    
    read -p "Push deletion to GitHub now? (y/n): " PUSH_CONFIRM
    if [[ "$PUSH_CONFIRM" == "y" ]]; then
        git add "$DESIGNS_DIR/$DELETE_NAME" "$MANIFEST_PATH" 2>/dev/null || git add "$MANIFEST_PATH"
        git commit -m "Delete design: $DELETE_NAME"
        git push
        echo "🚀 Changes pushed to GitHub!"
    fi

else
    # --- ADD MODE (Default) ---
    echo "--- Add New Design Mode ---"
    
    # 1. Prompt for Design Name (used for filename)
    read -p "Enter a unique filename for the design (e.g., modern_dark): " FILE_NAME
    if [[ -z "$FILE_NAME" ]]; then FILE_NAME="untitled_$(date +%s)"; fi
    [[ "$FILE_NAME" != *.json ]] && FILE_NAME="${FILE_NAME}.json"

    # 2. Prompt for Display Name (Label)
    read -p "Enter a Display Label for the UI [Default: $FILE_NAME]: " LABEL
    LABEL=${LABEL:-$FILE_NAME}

    # 3. Prompt for comma-separated labels (tags)
    read -p "Enter comma-separated tags (e.g., dark, minimalist, blue) [Default: null]: " TAGS
    TAGS=${TAGS:-"null"}

    # 4. Prompt for Text Description
    read -p "Enter a short description [Default: null]: " DESCRIPTION
    DESCRIPTION=${DESCRIPTION:-"null"}

    # 5. Prompt for Associated URL
    read -p "Enter associated website URL [Default: null]: " ASSOC_URL
    ASSOC_URL=${ASSOC_URL:-"null"}

    # 6. Prompt for Logo URL
    read -p "Enter Logo URL [Default: null]: " LOGO_URL
    LOGO_URL=${LOGO_URL:-"null"}

    # 7. Prompt for the actual JSON content (Multiline)
    echo "--------------------------------------------------------"
    echo "Paste your JSON content below."
    echo "Press ENTER then CTRL+D when finished:"
    echo "--------------------------------------------------------"
    JSON_CONTENT=$(cat)

    if [[ -z "$JSON_CONTENT" ]]; then
        echo "Error: JSON content cannot be empty."
        exit 1
    fi

    # Save the new design file
    mkdir -p "$DESIGNS_DIR"
    echo "$JSON_CONTENT" > "$DESIGNS_DIR/$FILE_NAME"
    echo "✅ Saved $DESIGNS_DIR/$FILE_NAME"

    # --- Update the Manifest via Python ---
    python3 -c "
import json, os

manifest_path = '$MANIFEST_PATH'
tags_raw = '$TAGS'
tags = [t.strip() for t in tags_raw.split(',')] if tags_raw != 'null' else None

new_entry = {
    'label': '$LABEL',
    'file': '$FILE_NAME',
    'tags': tags,
    'description': None if '$DESCRIPTION' == 'null' else '$DESCRIPTION',
    'url': None if '$ASSOC_URL' == 'null' else '$ASSOC_URL',
    'logo_url': None if '$LOGO_URL' == 'null' else '$LOGO_URL'
}

data = []
if os.path.exists(manifest_path) and os.path.getsize(manifest_path) > 0:
    with open(manifest_path, 'r') as f:
        try:
            data = json.load(f)
        except:
            data = []

data.append(new_entry)

with open(manifest_path, 'w') as f:
    json.dump(data, f, indent=2)
"
    echo "✅ Updated $MANIFEST_PATH"

    # --- Git Integration ---
    read -p "Push changes to GitHub now? (y/n): " PUSH_CONFIRM
    if [[ "$PUSH_CONFIRM" == "y" ]]; then
        git add "$DESIGNS_DIR/$FILE_NAME" "$MANIFEST_PATH"
        git commit -m "Add design: $LABEL"
        git push
        echo "🚀 Changes pushed to GitHub!"
    else
        echo "Inventory updated locally. Remember to push later."
    fi
fi
