#!/bin/bash

echo "Building the project..."
pip install setuptools
pip install -r requirements.txt
# Use python3 generically
export PATH=$PATH:/usr/local/bin

echo "Collect Static..."
python3 manage.py collectstatic --noinput --clear
python3 manage.py makemigrations
python3 manage.py migrate


echo "Build complete."
