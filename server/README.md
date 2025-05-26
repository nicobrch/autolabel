# AutoLabel Backend 🚀

This backend was created using FastAPI, SQLAlchemy and SQLite. Since it's main porpuse is to use SAM2 capabilities, the videos are stored on the file system and the DB stores metadata and valuable information.

## Installation

Create a virtual environment for the project. UV is highly recommended.

```shell
uv venv .venv
```

Then, activate this environment.

```shell
# On Windows
.venv\Scripts\activate
# On Linux
source .venv/bin/activate
```

Install project dependencies.

```shell
uv pip install -r requirements.txt
```

Download SAM2 model checkpoints directly from META.

```shell
cd checkpoints
download.sh
```

Finally, initialize the database

```shell
cd src
uv run db.py
```

## Usage

Once you completed the installation steps, you can run the server backend with:

```shell
cd src
uv run main.py
```
