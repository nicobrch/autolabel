# AutoLabel Backend 🚀

This backend was created using FastAPI, SQLAlchemy and SQLite. Since it's main porpuse is to use SAM2 capabilities, the videos are stored on the file system and the DB stores metadata and valuable information.

## Installation

Create a conda environment and install deps

```shell
conda create -n my_env --file requirements.txt
conda activate my_env
```

## Usage

```shell
cd server
uvicorn main:app --reload
```
