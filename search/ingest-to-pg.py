import sys
sys.path.insert(0, '.')

import os, psycopg2, json, argparse

argparser = argparse.ArgumentParser()
argparser.add_argument('--runmode','-r', help='readlimit')
args = argparser.parse_args()

from embeddingsaws import AWSEmbeddings
from Utils.utils import DateUtils
from datetime import datetime

class ReadData:
    def open_jsonl(self, filename, readlimit=None):
        listdata = []
        with open(filename, 'r') as data:
            for n,row in enumerate(data):
                listdata.append(row)
                if readlimit and n+1==readlimit:
                    return listdata
            return listdata

    def readjson(self, filename, readlimit=None):
        with open(filename, 'r') as f:
            loaded_file = json.load(f)
        if readlimit:
            loaded_file = loaded_file[:readlimit]
        return loaded_file

if args.runmode == 'prod':
    readlimit = None
    DB_URL = "postgresql://postgres:pass@pg_container:5432/vectordb"
else:
    readlimit = 10
    DB_URL = "postgresql://postgres:pass@pg_container:5432/vectordb"



create_table = """
CREATE TABLE IF NOT EXISTS table1 (
    id BIGINT PRIMARY KEY, 
    company TEXT,
    product TEXT, 
    fts_product tsvector generated always as (setweight(to_tsvector('english', coalesce(product, '')), 'A')) stored,
    feature TEXT,
    fts_feature tsvector generated always as (setweight(to_tsvector('english', coalesce(feature, '')), 'C')) stored,
    location TEXT, 
    content TEXT, 
    topic TEXT,  
    pub_date TIMESTAMP, 
    age_category TEXT, 
    content_embedding VECTOR(1536)
);
"""


class PGDBWork:

    def __init__(self, DB_URL):
        self.DB_URL = DB_URL
        self.conn = None
        self.DB_URL = DB_URL

    def create_connection(self):
        self.conn = psycopg2.connect(self.DB_URL)
        return self.conn

    def close_connection(self):
        if self.conn is not None and self.conn.closed == 0:
            self.conn.close()
        return

CONN = PGDBWork(DB_URL)
conn = CONN.create_connection()
cur = conn.cursor()

cur.execute(create_table)
conn.commit()

embed = AWSEmbeddings()
dateutils = DateUtils()
read_data = ReadData()

filename = './search/data/test_data.jsonl'
def read_data_file():
    readlimit = None
    all_data_read = read_data.open_jsonl(filename, readlimit)
    all_data = []
    for i in all_data_read:
        date = dateutils.convert_str_to_date(json.loads(i)['timestamp'])
        if date > datetime(2015, 1, 1):
            # i = json.loads(i)
            # print(f"\nheadline, {i['headline']}")
            all_data.append(i)

    return all_data

def write_to_db(data):
    count = 0
    inserted_row_count = 0
    print("")
    for dict_data in data:
        dict_data = json.loads(dict_data)
        count+=1
        if count % 1000 == 0:
            print("Writing to Postgres: ", count, " records processed.")
        conn = CONN.create_connection()
        cur = conn.cursor()
        id = dict_data['id']
        company = dict_data['company']
        product = dict_data['product']
        feature = dict_data['feature']
        location = dict_data['location']
        content = dict_data['content']
        topic = dict_data['topic']
        pub_date = dict_data['timestamp']
        age_category = dict_data['age_category']
        content_embedding = embed.get_embedding(content)
        data_to_insert = (id, company, product, feature, location, topic, pub_date, content, age_category, content_embedding)
        postgres_insert_query = """INSERT INTO table1 (id, company, product, feature, location, topic, pub_date, content, age_category, content_embedding) VALUES (%s, %s, %s, %s, %s, %s,  %s, %s, %s, %s)"""
        record_to_insert = (data_to_insert)
        try:
            cur.execute(postgres_insert_query, record_to_insert)
            conn.commit()
            inserted_row_count += 1
        except Exception as e:
            print(e)
            conn.rollback()
        finally:
            # Close the connection in case of any errors
            if conn is not None:
                conn.close()
    print("Total records inserted: ", inserted_row_count)

print("Writing to Postgres")
data = read_data.open_jsonl(filename, readlimit)
if data:
    print("Total records read: ", len(data))
    write_to_db(data)
    print("Writing to Postgres complete.")
else:
    print("No records to write to Postgres.")
CONN.close_connection()