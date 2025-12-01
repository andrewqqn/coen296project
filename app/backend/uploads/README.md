# Uploads Directory

This directory stores uploaded files (like PDF receipts) when running in **emulator mode**.

## Directory Structure

```
uploads/
└── receipts/
    └── {user_id}/
        ├── {uuid1}.pdf
        ├── {uuid2}.pdf
        └── ...
```

## Modes

### Emulator Mode (Development)
When `USE_FIRESTORE_EMULATOR=true`:
- Files are saved locally in this directory
- File URLs use format: `local://uploads/receipts/{user_id}/{filename}`
- Files persist on local disk for testing

### Production Mode
When `USE_FIRESTORE_EMULATOR=false`:
- Files are uploaded to Firebase Storage
- File URLs are public Firebase Storage URLs
- This directory is not used

## Git Ignore

This directory is included in `.gitignore` to prevent uploaded files from being committed to version control.
