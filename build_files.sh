#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Collect static files into the STATIC_ROOT directory
python manage.py collectstatic --noinput

# Create the build directory for Vercel if it doesn't exist
mkdir -p staticfiles_build
cp -r staticfiles/* staticfiles_build/