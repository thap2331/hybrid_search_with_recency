import sys
sys.path.insert(0, '.')

import argparse
import psycopg2
from Utils.utils import PGDBWork
from embeddingsaws import AWSEmbeddings

parser = argparse.ArgumentParser(description='Search options', add_help=False)
parser.add_argument('-c', '--combo', action='store_true', help='Perform combo search')
parser.add_argument('-h', '--hybrid', action='store_true', help='Perform hybrid search')
args = parser.parse_args()

print('all args:', args)
if args.combo:
    print("Performing hybrid search with recency...")
    sql_query = """
                    SELECT * FROM 
                    combo_search(%s,%s::vector(1536), %s);
                """
elif args.hybrid:
    # Perform hybrid search
    print("Performing hybrid search...")
    sql_query = """
                    SELECT * FROM 
                    hybrid_search(%s,%s::vector(1536), %s);
                """
else:
    raise ValueError("No valid search option provided. Use --combo (-c) or --hybrid (-h).")

DB_URL = "postgresql://postgres:pass@pg_container:5432/vectordb"

CONN = PGDBWork(DB_URL)
conn = CONN.create_connection()
cursor = conn.cursor()

create_embeddings = AWSEmbeddings()

# Your query embedding
query="clean energy solution"
query_embedding = create_embeddings.get_embedding(query) #np.random.rand(1536).tolist()  # Replace with your actual query embedding
print('\n',query,query_embedding[0:5],'\n')

# Query to find the most similar documents (e.g., top 5 closest vectors)
cursor.execute(
    sql_query,
    (query, query_embedding, 5)
)

# Fetch the results
results = cursor.fetchall()

# Print the results
for row in results:
    # print(row,'\n')
    print(f"ID: {row[0]}, company: {row[1]}, product: {row[2]}, fts_product: {row[3]}, feature: {row[4]}, fts_feature: {row[5]}, location: {row[6]}, content: {row[7]}, topic: {row[8]}, pub_date: {row[9]}, age_category: {row[10]}, combined_rank: {row[12]}, rankings: {row[13]}")
    print('\n')

# Close the connection
cursor.close()
conn.close()
