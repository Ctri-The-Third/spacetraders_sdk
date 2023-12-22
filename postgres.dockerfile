FROM postgres:latest

ENV POSTGRES_USER=spacetraders
run mkdir -p /docker-entrypoint-initdb.d 

copy ./PostgresSchema.SQL /docker-entrypoint-initdb.d/postgresschema.sql

