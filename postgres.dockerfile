FROM postgres:16.1

ENV POSTGRES_USER=spacetraders
ENV ST_DB_NAME = spacetraders
run mkdir -p /docker-entrypoint-initdb.d 


copy ./PostgresConfig.SQL /docker-entrypoint-initdb.d/postgresconfig.sql
# copy ./postgresql.conf /var/lib/postgresql/data/postgresql.conf
copy ./PostgresSchema.SQL /docker-entrypoint-initdb.d/postgresschema.sql
#cp /usr/share/postgresql/postgresql.conf /var/lib/postgresql/data/postgresql.conf
 
 # run pg_restore -U spacetraders -d spacetraders /docker-entrypoint-initdb.d/postgresschema.sql

cmd ["postgres" ] 