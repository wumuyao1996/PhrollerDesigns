# Adventures Library

This directory contains the adventure maps and scenarios (.phvtt) for the Phroller project.

## Directory Structure

- `manifest.json`: The index of all available adventures.
- `files/`: Contains the actual `.phvtt` or related map files.

## Manifest Entry Format

When populating `manifest.json`, each entry should follow this structure:

```json
{
  "label": "Display Name of Adventure",
  "file": "filename.phvtt",
  "author": "Artist Name",
  "url": "https://link-to-artist-portfolio.com",
  "description": "A short description of the adventure.",
  "tags": [
    "tag1",
    "tag2",
    "map"
  ],
  "date_added": "YYYY-MM-DDTHH:MM:SS.000Z"
}
```
