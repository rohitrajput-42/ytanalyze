#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run collectstatic to gather all static files
python manage.py collectstatic --noinput

# Move static files to the correct directory for Vercel
mkdir -p staticfiles_build
cp -r staticfiles/* staticfiles_build/