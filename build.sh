#!/bin/bash

echo "Building the project..."

# Vercel installs requirements automatically, but we can ensure they are there.
# python3.9 -m pip install -r requirements.txt

echo "Collect Static..."
python3.9 manage.py collectstatic --noinput --clear

echo "Build complete."
