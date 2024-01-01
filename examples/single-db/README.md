## Ellar SQLAlchemy Single Database Example
Project Description

## Requirements
Python >= 3.7
Starlette
Injector

## Project setup
```shell
pip install poetry
```
then, 
```shell
poetry install
```
### Apply Migration
```shell
ellar db upgrade
```

### Development Server
```shell
ellar runserver --reload
```
then, visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)