# freeze packages to requirements.txt
pip freeze > requirements.txt 
or
pip freeze | Set-Content -Encoding ascii requirements.txt

# run the app
uvicorn main:app --port {port} --reload

# create migrations
alembic revision --autogenerate -m "message"

# run migrations
alembic upgrade head