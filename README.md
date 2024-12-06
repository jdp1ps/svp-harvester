# svp-harvester

Sovisu+ publications harvester as microservice

SoVisu+ Harvester is distributed under the terms of the [CeCILL v2.1 license](http://www.cecill.info/licences/Licence_CeCILL_V2.1-fr.txt) (GPL compatible).

:warning: This project is still in development and is not yet ready for production.

## Overview

### Goals

The SoVisu+ Harvester project is intended to provide a unified interface to the various scholarly publication databases
and repositories
that are used by an institutional research information system in general and the SoVisu+ project in particular.

SoVisu+ Harvester is implemented as a microservice that can be deployed in a containerized environment.

It is intended to institutions that have already created and actively maintain a repository of matched identifiers for
authors, structures and research projects.

### Overall use

The SoVisu+ Harvester is designed to receive requests containing a list of identifiers for a so-called "research
entity" (wich can be an author, research structure, research institution or research project) and to return a list of references to publications
that are associated with the research entity.

The list of accepted identifiers is not exhaustive as the service is extensible by design.

- Idref
- Idhal
- ORCID
- ResearcherID
- ...

The references are obtained through a set of modular harvesters that are designed to query various scholarly publication
databases and repositories :

- Data.idref.fr
- Hal
- Scanr
- Web of Science
- OpenAlex
- ...
  The harvesters are launched in parallel and their results are returned on the fly to the client, allowing for a fast
  response
  time and an asynchronous display of the results.

![svp-harvester overall behavior](img/svp-harvester-overall-behavior.png?raw=true "Overall behavior")

Requests and results are registered in the database for monitoring purposes. The harvesting history may be consulted
through the web interface.

### Input

The research entities may be submitted to the harvester in 4 ways :

- Manually, through the web interface
- By querying the REST API asynchronoulsy
- By querying the REST API synchronoulsy
- Through AMQP messages delivered through a message broker (such as RabbitMQ)

### Output

The structure of the JSON output complies with
the [SciencePlus publications model](https://documentation.abes.fr/aidescienceplusabes/index.html#ModeleDonnees).

Please note that references deduplication is out of scope of SoVisu+ Harvester and should be handled by another SoVisu+
component.

## Technical overview

### Used technologies

Server side :

- Python 3.10 with asyncio
- FastAPI with Pydantic
- PostgreSQL with asyncpg and alembic
- RabbitMQ (through aio-pika)
- Poetry
- Pytest
- Black

Client side (admin interface) :

- Npm
- Webpack
- Bootstrap
- Jest

## Development ressources (installation outside of a containerized environment)

### Basic requirements

Install Postgresql, RabbitMQ and the web server you want to use as a front-end.

Note that poetry is not required as requirements are exported to requirements.txt.

Clone the projet, copy .env.example to .env and .test.env and update them. All the values defined in the app/settings
classes (AppSettings, TestSettings, DevSettings...)
can be overriden either through .env files or through environment variables (the latter takes precedence over the
former).

### Database configuration

#### Database creation

As postgres user :

```sql
CREATE
DATABASE your_db_name;
CREATE
USER your_user_name WITH PASSWORD 'your_secret';
GRANT ALL PRIVILEGES ON DATABASE
your_db_name to your_user_name;
```

Repeat for test database.

Update .env and .test.env with credentials

```bash
DB_USER="your_user_name"
DB_NAME="your_db_name"
DB_PASSWORD="your_secret"
```

#### Database migration

The project uses [alembic](https://alembic.sqlalchemy.org/en/latest/) for schema versioning and migration.

At development time, migrations are generated automatically from the models (see app/models and alembic/versions).

```bash
APP_ENV=DEV alembic revision --autogenerate -m "Explain what you did to the model"
```

At deployment time, migrations are applied to the database.

```bash
APP_ENV=DEV alembic upgrade head
``` 

### Dependencies installation

The project uses [poetry](https://python-poetry.org/) for dependency management.

```bash
poetry install
```

### Tests

The project uses [pytest](https://docs.pytest.org/en/stable/) for testing.

From project root :

```bash
APP_ENV=TEST pytest
```

or with coverage

```bash
APP_ENV=TEST coverage run --source=app -m pytest
coverage report --show-missing
```

### Assets compilation

The project uses [webpack](https://webpack.js.org/) for assets compilation.

Copy app/templates/src/js/env.js.example to app/templates/src/js/env.js and update it with your values before compiling
the assets.

From app/templates :

- Dependencies installation

```bash
npm install
```

- Assets compilation

```bash

npm run build

```

or

```bash
npm run build
```

### Launch

From project root :

```bash
APP_ENV=DEV uvicorn app.main:app --reload
```

or

```bash
APP_ENV=DEV python3 app/main.py 
```

# I18N Templates

To update the translation files, run the following command from the project root :

```bash
pybabel extract --mapping babel.cfg --output-file=locales/admin.pot .
```

To init a po file for a new language :

```bash
pybabel init --domain=admin --input-file=locales/admin.pot --output-dir=locales --locale=NEW_one
```

To update the .po files with the new strings :

```bash
pybabel update --domain=admin --input-file=locales/admin.pot --output-dir=locales
```

To compile the .po files to .mo files :

```bash
pybabel compile --domain=admin --directory=locales --use-fuzzy
```

See [Babel commad line documentation](https://babel.pocoo.org/en/latest/cmdline.html) for more information.

# Documentation compilation and publication

The documentation is written in reStructuredText and compiled with Sphinx.

## HTML publication

To export the documentation to HTML, run the following command from the `docs` directory :

```bash
python -m sphinx -b html source build/html
```

Then, copy the content of the `docs/build/html` directory to the server of your choice.

## ReadTheDocs publication

The documentation is automatically published on [ReadTheDocs](https://svp-harvester.readthedocs.io/en/latest/overview.html) at each push on the `dev-main`
branch.
The configuration settings are defined in the `docs/source/conf.py` file, which is specified in the `.readthedocs.yml` file as the entry point.

## Confluence publication

To export the documentation to Confluence through the Confluence Publisher plugin,

- Copy `docs/source/confluence/conf.py.example` to `docs/source/confluence/conf.py` and update it with your values
- Run the following command from the `docs` directory :

```bash
python -m sphinx -b confluence -c source/confluence source build/confluence -E -a
```
