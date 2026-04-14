web: python manage.py migrate --run-syncdb && python manage.py loaddata home/fixtures/gsu_buildings.json && gunicorn smartcommute.wsgi --bind 0.0.0.0:$PORT
