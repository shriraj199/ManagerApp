#!/bin/bash

echo "Building the project..."

# Use python3 generically
export PATH=$PATH:/usr/local/bin

echo "Collect Static..."
python3 manage.py collectstatic --noinput --clear

echo "Build complete."
