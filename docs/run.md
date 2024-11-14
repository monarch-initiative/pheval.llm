# Grounding
Since LLMs today, up to November 2024, show little ability to precisely and reliably return unique identifiers of some entity present in a database, we need to deal with this issue. In order to transform some human language disease name such as "cystic fibrosis" into its corresponding [OMIM identifier OMIM:219700](https://omim.org/entry/219700) we use the following approach:

<!--- Add links to files as soon as they are merged--->
1. First, we try exact lexical matching between the LLMs reply and the OMIM diseases label.
2. Then we run [CurateGPT](https://github.com/monarch-initiative/curategpt) on the remaining ones that have not been grounded.

We remark here that we ground to MONDO.

# OntoGPT