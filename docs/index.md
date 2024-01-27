<style>
.md-content .md-typeset h1 { display: none; }
</style>
<p align="center">
  <a href="#" target="blank"><img src="https://python-ellar.github.io/ellar/img/EllarLogoB.png" width="200" alt="Ellar Logo" /></a>
</p>
<p align="center">EllarSQL is an SQL database Ellar Module.</p>

![Test](https://github.com/python-ellar/ellar-sql/actions/workflows/test_full.yml/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/python-ellar/ellar-sql)
[![PyPI version](https://badge.fury.io/py/ellar-sql.svg)](https://badge.fury.io/py/ellar-sql)
[![PyPI version](https://img.shields.io/pypi/v/ellar-sql.svg)](https://pypi.python.org/pypi/ellar-sql)
[![PyPI version](https://img.shields.io/pypi/pyversions/ellar-sql.svg)](https://pypi.python.org/pypi/ellar-sql)

EllarSQL is an SQL database module, leveraging the robust capabilities of [SQLAlchemy](https://www.sqlalchemy.org/) to 
seamlessly interact with SQL databases through Python code and objects.

EllarSQL is meticulously designed to streamline the integration of **SQLAlchemy** within your 
Ellar application. It introduces discerning usage patterns around pivotal objects 
such as **model**, **session**, and **engine**, ensuring an efficient and coherent workflow.

Notably, EllarSQL refrains from altering the fundamental workings or usage of SQLAlchemy. 
This documentation is focused on the meticulous setup of EllarSQL. For an in-depth exploration of SQLAlchemy, 
we recommend referring to the comprehensive [SQLAlchemy documentation](https://docs.sqlalchemy.org/).

## **Feature Highlights**
EllarSQL comes packed with a set of awesome features designed:

- **Migration**: Enjoy an async-first migration solution that seamlessly handles both single and multiple database setups and for both async and sync database engines configuration.

- **Single/Multiple Database**: EllarSQL provides an intuitive setup for models with different databases, allowing you to manage your data across various sources effortlessly.

- **Pagination**: EllarSQL introduces SQLAlchemy Paginator for API/Templated routes, along with support for other fantastic SQLAlchemy pagination tools.

- **Unlimited Compatibility**: EllarSQL plays nice with the entire SQLAlchemy ecosystem. Whether you're using third-party tools or exploring the vast SQLAlchemy landscape, EllarSQL seamlessly integrates with your preferred tooling.

## **Requirements**
EllarSQL core dependencies includes:

- Python >= 3.8
- Ellar >= 0.6.7
- SQLAlchemy >= 2.0.16
- Alembic >= 1.10.0

## **Installation**

```shell
pip install ellar-sql
```

## **Quick Example**
Let's create a simple `User` model.
```python
from ellar_sql import model


class User(model.Model):
    id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)
    username: model.Mapped[str] = model.mapped_column(model.String, unique=True, nullable=False)
    email: model.Mapped[str] = model.mapped_column(model.String)
```
Let's create `app.db` with `User` table in it. For that we need to set up `EllarSQLService` as shown below:

```python
from ellar_sql import EllarSQLService

db_service = EllarSQLService(
    databases='sqlite:///app.db', 
    echo=True, 
)

db_service.create_all()
```
If you check your execution directory, you will see `sqlite` directory with `app.db`.

Let's populate our `User` table. To do, we need a session, which is available at `db_service.session_factory`

```python
from ellar_sql import EllarSQLService, model


class User(model.Model):
    id: model.Mapped[int] = model.mapped_column(model.Integer, primary_key=True)
    username: model.Mapped[str] = model.mapped_column(model.String, unique=True, nullable=False)
    email: model.Mapped[str] = model.mapped_column(model.String)


db_service = EllarSQLService(
    databases='sqlite:///app.db',
    echo=True,
)

db_service.create_all()

session = db_service.session_factory()

for i in range(50):
    session.add(User(username=f'username-{i+1}', email=f'user{i+1}doe@example.com'))


session.commit()
rows = session.execute(model.select(User)).scalars()

all_users = [row.dict() for row in rows]
assert len(all_users) == 50

session.close()
```

We have successfully seed `50` users to `User` table in `app.db`. 

You can find the source code 
for this example 
[here](https://github.com/python-ellar/ellar-sql/blob/master/examples/index-script/main.py){target="_blank"}.

I know at this point you want to know more, so let's dive deep into the documents and [get started](./overview/index.md).
