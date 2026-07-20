#!/bin/bash

# Define the root of the archives
ARCHIVE_ROOT="/home/rajinderj8888/personavault/backend/archive"

echo "Cleaning up redundant archive folders in $ARCHIVE_ROOT..."

if [ -d "$ARCHIVE_ROOT" ]; then
    # List of known redundant folders based on your project structure
    REDUNDANT_FOLDERS=("a" "3.11.11" "#" "Python" "Create" "with" "new")

    for folder in "${REDUNDANT_FOLDERS[@]}"; do
        TARGET="$ARCHIVE_ROOT/$folder"
        if [ -d "$TARGET" ]; then
            echo "Removing $TARGET..."
            rm -rf "$TARGET"
        fi
    done
    
    # Check if the archive directory is empty and remove it if so
    if [ -d "$ARCHIVE_ROOT" ] && [ -z "$(ls -A "$ARCHIVE_ROOT" 2>/dev/null)" ]; then
       echo "Removing empty archive root..."
       rm -rf "$ARCHIVE_ROOT"
    fi
else
    echo "Archive directory not found: $ARCHIVE_ROOT"
fi

echo "Cleanup complete. It is recommended to use a virtual environment (venv) for dependencies instead."