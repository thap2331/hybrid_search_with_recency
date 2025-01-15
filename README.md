# Hybrid search with recency
- 

## Spin up containers
- Start by spinning up the containers. You can do `docker compose up -d`. It will start postgres db in docker, worker instance from which we can run various commands, and  pgweb which will allow us to see the data visually as well as run queries as needed.

## Create vector extension
- Option 1:
    - ```sh
        docker exec -it pg_container psql -U postgres -d vectordb -c "CREATE EXTENSION IF NOT EXISTS vector;"
        ```
- Option 2:
    - Go to `http://localhost:8002/` and run a extension query:
        - `create extension if not exists vector;`


## Ingest data to postgres
- ```sh
    docker exec -t worker bash -c "python ./search/ingest-to-pg.py -r prod"
    ```

## See data

# Create functions
### Count the number of functions
- ```sh
    docker exec -t pg_container psql -U postgres -d vectordb -c "SELECT COUNT(*) FROM pg_proc WHERE pronamespace = 'public'::regnamespace;"
    ```

# Copy sql file that contains the functions
### copy hybrid and combo retrieval sql files
```sh
    docker cp ./search/hybrid-retrieval.sql pg_container:/home/hybrid-retrieval.sql && docker cp ./search/combo-retrieval.sql pg_container:/home/combo-retrieval.sql
```

### Add functionality to do these searches
```sh
    docker exec -t pg_container psql -U postgres -d vectordb -f /home/hybrid-retrieval.sql
```

```sh
    docker exec -t pg_container psql -U postgres -d vectordb -f /home/combo-retrieval.sql
```



## Time to run search
```bash
    docker exec -t worker bash -c "python ./search/search.py -c"
```

```sh
    docker exec -t worker bash -c "python ./search/search.py -h"
```


## Go inside the db container
- `docker exec -it pg_container bash -c "psql -U postgres -d vectordb"`