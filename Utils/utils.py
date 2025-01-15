import json, os
# import boto3
import psycopg2
#requests
from datetime import datetime

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
    
class DateUtils:

    def convert_str_to_date(self, date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%f')
        except:
            date_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        finally:
            pass
        return date_obj

class ReadData:

    def open_jsonl(self, filename, readlimit=None):
        listdata = []
        with open(filename, 'r') as data:
            for n,row in enumerate(data):
                listdata.append(row)
                if readlimit and n+1==readlimit:
                    return listdata
            return listdata

    def readjson(self, filename):
        with open(filename, 'r') as f:
            loaded_file = json.load(f)
        return loaded_file

class S3Utils:

    def __init__(self):
        self.s3 = boto3.client('s3')

    def download_all_s3_bucket_folder(self, bucket_name, folder_prefix, local_folder):
        # List objects in the specified folder
        objects = self.s3.list_objects(Bucket=bucket_name, Prefix=folder_prefix)

        # Download each object in the folder
        for obj in objects.get('Contents', []):
            file_name = obj['Key']
            local_file_path = os.path.join(local_folder, file_name)
            self.s3.download_file(bucket_name, file_name, local_file_path)
            print(f"Downloaded: {file_name} to {local_file_path}")

    def download_file_from_s3(self, bucket_name, folder_prefix, local_folder):
        local_file_path = local_folder + file_name
        s3.download_file(bucket_name, folder_prefix + file_name, local_file_path)
        print(f"Downloaded: {file_name} to {local_file_path}")

class MetricsCollectionUtils:

    def __init__(self):
        self.sponsor_list = json.loads(requests.get("https://cdn.texastribune.org/sponsors.json").text)

    def get_words_count(self, article):

        return len(article.split(' '))

    def break_into_less_than_512_tokens(self, article):
        sentences = []
        count = 0
        partial_sentence = ''

        for sentence in article.split('.'):
            if sentence.strip():
                count += 1
                partial_sentence += sentence.strip() + '.'
                if count == 15:
                    sentences.append(partial_sentence)
                    partial_sentence = ''
                    count = 0

        if partial_sentence:
            sentences.append(partial_sentence)

        return sentences
        

    def legacy_org_extraction(self, article):
        try:
            lower_case_fulltext = article.casefold()
            problem_titles = ['USI', 'Every Texan', 'Economist', 'Texas AFT', 'Unclaimed Property']
            sponsors = []
            for sp in self.sponsor_list:
                if sp['name'] in problem_titles:
                    if sp['space_names'] in article:
                        sponsors.append(sp['name'])
                else:
                    if sp['space_names'].casefold() in lower_case_fulltext:
                        sponsors.append(sp['name'])
            if not sponsors:
                return []
            
        except Exception as e:
            print('Error when getting sponsor list for article %s: %s' % (article, e))
            return None
        return sponsors

    def make_post_request(self, url, json_data):
        resp = requests.post(url, json=json_data)
        if resp.status_code != 200:
            raise Exception(f"Error: {resp.status_code}")
        ml_extracted_entities = json.loads(json.loads(resp.text))

        return ml_extracted_entities
  