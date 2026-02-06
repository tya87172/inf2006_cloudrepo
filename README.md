# COE Seasonality (FastAPI + SQLite)

Small proof-of-concept for exploring COE seasonality by vehicle category, year range, and aggregation (mean/median). Data is stored in SQLite and queried via FastAPI.

## Prerequisites

- Python 3.11+

## Setup

1) Create the database from the CSV:

```sh
python db/init_db.py
```

2) Run the API server:

```sh
uvicorn main:app --reload
```

## API

- `GET /seasonality`
  - Query params:
    - `vehicle_class` (e.g. `Category A`)
    - `start_year` (e.g. `2010`)
    - `end_year` (e.g. `2019`)
    - `aggregation` (`mean` or `median`)

Example:

```sh
curl "http://127.0.0.1:8000/seasonality?vehicle_class=Category%20A&start_year=2010&end_year=2019&aggregation=mean"
```

## Optional UI

If you add a simple `static/index.html` and serve it from FastAPI, open:

```
http://127.0.0.1:8000/
```
# INF2006 Cloud Project

This repository contains the backend infrastructure and deployment pipelines...

### Project Structure
```text
/home/ec2-user/
└── project/                <-- deployment target
    ├── .git/                
    ├── .github/             
    │   └── workflows/
    │       └── deploy.yml
    └── README.md           <-- Documents your setup
