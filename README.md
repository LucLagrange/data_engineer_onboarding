# What is this?

A small-scale data engineering pipeline that extracts data from OpenWeather API and loads it into a Postgres instance with two available methods.

## Setup

### 1.Set the variables

Write all your variables in a .env file and use the following command to export them all at once:

```bash
export $(grep -v '^#' .env | xargs)
```

### 2. Create the Network

Create the bridge network to allow our containers to talk to each other:

```bash
docker network create weather_network
```

### 2. Build and run the Postgres container

```bash
cd server/
docker compose build
docker compose up -d
```

### 3. Build and run the fetch & export containers  

Depending on which method you want to try:

1. "Classic" python method with requests and psycopg

```bash
cd client-1-python
docker compose build
docker compose up
```

2. dltHub method

```bash
cd client-2-dlthub
docker compose build
docker compose up
```

### 4. Check the rows inserted to Postgres

1. Jump into the container:

```bash
docker exec -it postgres_weather_instance psql -U <user> -d <database>
```

2. Check the latest rows:

For the first method (python):

```SQL
SELECT * FROM weather_metrics;
```

For the second method (dlthub, different schema):

```SQL
SELECT * FROM raw_weather_data.weather_report;
```

## To improve/finish

- Try to load both methods on same schema and table with a "source" column to differentiate.
- Better timestamp handling (local vs utc)
- Orchestration with Cron or Airflow
- Smaller Dockerfile (Postgres-alpine?) and smarter build (see best practices)
- Try with Duckdb!
