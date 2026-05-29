# GLB Models Collection

This directory contains the GLB asset designs for the Phroller project.

## Directory Structure

- `manifest.json`: The index of all available GLB models.
- `designs/`: Contains the JSON configuration files for each model.
- `images/`: Contains the preview images (e.g., PNG/JPG) for each model.
- `files/`: Contains the actual `.glb` 3D model files.

## Manifest Entry Format

When populating `manifest.json`, each entry should follow this structure:

```json
{
  "id": "unique_model_id",
  "label": "Display Name of Model",
  "file": "design_file_name.json",
  "author": "Artist Name",
  "description": "A short description of the model.",
  "artist_url": "https://link-to-artist-portfolio.com",
  "tags": [
    "tag1",
    "tag2",
    "3d",
    "prop"
  ],
  "preview_url": "https://wumuyao1996.github.io/PhrollerDesigns/assets/models/images/preview.png",
  "model_url": "https://wumuyao1996.github.io/PhrollerDesigns/assets/models/files/model.glb" 
}
```

Make sure to include the `author` and `tags` fields as requested.
