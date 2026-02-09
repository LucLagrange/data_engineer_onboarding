# What is this?

A small-scale data engineering pipeline that extracts data from OpenWeather API and loads it into a Postgres instance.

## Setup

### 1.Set the variables

Write all your variables in a .env file and use the following command to export them all at once:

```bash
export $(grep -v '^#' .env | xargs)
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
cd client-1
docker compose build
docker compose up
```

2. dltHub method

```bash
cd client-2
docker compose build
docker compose up
```

### 4. Check the rows inserted to Postgres

1. Jump into the container:

```bash
docker exec -it postgres_weather_instance psql -U <user> -d <database>
```

2. Check the latest rows:

```SQL
SELECT * FROM weather_metrics ORDER BY observed_at DESC LIMIT 5;
```
