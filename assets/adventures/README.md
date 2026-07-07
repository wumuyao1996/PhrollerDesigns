# Adventures Library

This directory contains the adventure maps and scenarios (.phvtt) for the Phroller project.

## Directory Structure

- `manifest.json`: The index of all available adventures.
- `files/`: Contains the actual `.phvtt` or related map files.

## Manifest Entry Format

When populating `manifest.json`, each entry should follow the `AdventureManifest` model format from the Phroller app:

```json
{
  "id": "unique_adventure_id",
  "title": "Display Name of Adventure",
  "description": "A short description of the adventure.",
  "bundleUrl": "https://assets.phroller.com/adventures/files/filename.phvtt",
  "previewImageUrl": "https://assets.phroller.com/adventures/images/preview.jpg",
  "tags": [
    "tag1",
    "tag2",
    "map"
  ],
  "artistUrls": {
    "Artist Name": "https://link-to-artist-portfolio.com"
  },
  "version": 1.0
}
```
