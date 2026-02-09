# Use the official PostgreSQL 18 image
FROM postgres:18

# Avoid in production, only for testing
ENV POSTGRES_DB=weather_db
ENV POSTGRES_USER=weather_user
ENV POSTGRES_PASSWORD=weather_pass

# Any .sql script in this folder runs automatically on the FIRST container start
COPY init.sql /docker-entrypoint-initdb.d/

# Expose the default Postgres port
EXPOSE 5432