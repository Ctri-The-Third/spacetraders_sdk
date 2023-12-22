docker build -f postgres.dockerfile -t straders_db .
docker run --name spacetraders_db -e POSTGRES_PASSWORD=mysecretpassword  -d straders_db