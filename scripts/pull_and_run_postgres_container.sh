docker pull ctriatanitan/spacetraders_db:latest
docker network create spacetraders-network

docker run --name spacetraders_db_instance --network="spacetraders-network" --env-file scripts\.env   -p 6432:5432 -d spacetraders_db 
