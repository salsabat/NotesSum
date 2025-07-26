import pinecone
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os


load_dotenv()
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')


class PCDB:

    def __init__(self, index_name):
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        if index_name not in self.pc.list_indexes().names():
            self.pc.create_index(index_name, dimension=384, metric="cosine", spec=ServerlessSpec(
                cloud="aws", region="us-east-1"))
        self.index = self.pc.Index(index_name)

    def insert_index(self, vectors):
        try:
            self.index.upsert(vectors=vectors)
            return True
        except:
            return False

    def query(self, query_v, top_k=3, filter=None):
        return self.index.query(vector=query_v, top_k=top_k, filter=filter, include_metadata=True)
