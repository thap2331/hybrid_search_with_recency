from openai import OpenAI
import boto3
import json
from langchain.text_splitter import CharacterTextSplitter

from Utils.utils import ReadData

client = OpenAI()


#Create the connection to Bedrock
bedrock = boto3.client(
    service_name='bedrock',
    region_name='us-east-1', 
)

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1',
    
)

class OPENAIEmbeddings:

    def get_embedding(self, text, model="text-embedding-3-large"):
        text = text.replace("\n", " ")
        return client.embeddings.create(input = [text], model=model).data[0].embedding

class AWSEmbeddings:
    
    def get_embedding(self, text):
        body = json.dumps({
            "inputText": text,
        })

        model_id = 'amazon.titan-embed-text-v1'
        accept = 'application/json'
        content_type = 'application/json'

        # Invoke model
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId=model_id,
            accept=accept,
            contentType=content_type
        )

        # Print response
        response_body = json.loads(response['body'].read())
        embedding = response_body.get('embedding')
        
        return embedding
    
    def split_and_get_embeddings(self, text):
        text_chunks = createChunks().split_text(text)
        chunks_and_embeddings = []
        for chunk in text_chunks:
            chunks_and_embeddings.append([chunk, self.get_embedding(chunk)])
        
        return chunks_and_embeddings
    

class createChunks:
        
    def split_text(self, text):

        # Initialize the text splitter
        splitter = CharacterTextSplitter(separator=" ", chunk_size=1000, chunk_overlap=100)

        # Split the text
        text_chunks = splitter.split_text(text)

        # Display the chunks
        for i, chunk in enumerate(text_chunks):
            print(f"Chunk {i + 1}:\n{chunk}\n")
        
        return text_chunks
