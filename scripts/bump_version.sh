#!/bin/bash
cd /home/rajinderj8888/personavault/backend
CURRENT=$(cat app/version.txt)
MINOR=$(echo $CURRENT | cut -d. -f2)
PATCH=$(echo $CURRENT | cut -d. -f3)
NEW_PATCH=$((PATCH + 1))
NEW_VERSION="1.$MINOR.$NEW_PATCH"
echo $NEW_VERSION > app/version.txt
echo "✅ Version bumped to $NEW_VERSION"
