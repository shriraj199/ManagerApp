#!/bin/bash

echo "Building the project..."

pip install setuptools
pip install -r requirements.txt

echo "Collect Static..."
python3 manage.py collectstatic --noinput --clear

echo "Running migrations..."
python3 manage.py migrate

echo "Build complete."