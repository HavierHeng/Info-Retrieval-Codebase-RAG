# Graph Metadata
This just graphs out the metadata in a Neo4J database. There might be some further use case with graph queries via LLM.

## Installation
Easiest if Neo4J is installed in a docker container, you may follow the instructions here: https://neo4j.com/docs/operations-manual/current/docker/introduction/#getting-docker-image

In short, start Neo4J like this to have persistent data.
```
docker run -d \
    -p 7474:7474 -p 7687:7687 \
    -v $PWD/data:/data -v $PWD/plugins:/plugins \
    --name neo4j-apoc \
    -e NEO4J_apoc_export_file_enabled=true \
    -e NEO4J_apoc_import_file_enabled=true \
    -e NEO4J_apoc_import_file_use__neo4j__config=true \
    -e NEO4JLABS_PLUGINS=\[\"apoc\"\] \
    neo4j
```

## Helpful Cypher commands for displaying the content of the graph
Limit the listing of all nodes: `MATCH(n) RETURN n LIMIT 25`
Wipe database: `MATCH(n) DETACH DELETE n`

## Graph retriever
This uses an LLM to generate Cypher queries which then retrieve the data from the graph. The goal for this initial retriever is to find the files that best answer the query, so that it can be indexed, and then can be further reduced by means of BM25 or embeddings.
