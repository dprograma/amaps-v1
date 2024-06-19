#!/bin/bash

# Apply migrations
python manage.py migrate

# Start the Django server
python manage.py runserver 0.0.0.0:8003
