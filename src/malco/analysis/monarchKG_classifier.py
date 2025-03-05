# Monarch KG
# Idea: for each ppkt, make contingency table NF/F and in box write
# average number of connections. Thus 7 K of entries with num_edges, y=0,1
# Think about mouse weight and obesity as an example.
import numpy
from neo4j import GraphDatabase

# Connect to the Neo4j database
bolt_url = "bolt://neo4j-bolt.monarchinitiative.org"
driver = GraphDatabase.driver(bolt_url)

# From results take ppkts ground truth correct result and 0,1
# Map OMIM to MONDO
#
# Need to decide what to project out. Maybe simply all edges connected to the MONDO terms I have.
# At this point for each MONDO term I have count the edges
# Define the Cypher query
query = """
MATCH
(upheno:`biolink:PhenotypicFeature` WHERE upheno.id STARTS WITH "UPHENO:")<-[:`biolink:subclass_of`]-(phenotype:`biolink:PhenotypicFeature`)<-[gena:`biolink:has_phenotype`]-(gene:`biolink:Gene`)-[:`biolink:orthologous_to`]-(human_gene:`biolink:Gene` WHERE "NCBITaxon:9606" IN human_gene.in_taxon)
RETURN 
    upheno.id, """

# Run query
data = []
with driver.session() as session:
    results = session.run(query)
    for record in results:
        data.append(record)
