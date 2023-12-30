FROM postgres:latest

ENV POSTGRES_USER=spacetraders
run mkdir -p /docker-entrypoint-initdb.d 

copy ./postgresql.conf /postgresql.conf 
copy ./PostgresSchema.SQL /docker-entrypoint-initdb.d/postgresschema.sql



cmd ["postgres", "-c" , "config_file=/postgresql.conf"] 