# Graph Metadata
This just graphs out the metadata in a Neo4J database. There might be some further use case with graph queries via LLM.

## Installation
Easiest if Neo4J is installed in a docker container, you may follow the instructions here: https://neo4j.com/docs/operations-manual/current/docker/introduction/#getting-docker-image

In short, start Neo4J like this to have persistent data.
```
docker run -d \
    --publish=7474:7474 --publish=7687:7687 \
    --volume=$HOME/neo4j/data:/data \
    neo4j
```


