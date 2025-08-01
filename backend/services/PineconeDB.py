import pinecone
from dotenv import load_dotenv
import os


load_dotenv()
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')


class PCDB:

    def __init__(self, index_name, force_recreate=False):
        # Initialize Pinecone with new API (pinecone==7.3.0)
        self.pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
        
        # If force_recreate is True, delete the existing index
        if force_recreate and index_name in self.pc.list_indexes().names():
            print(f"Deleting existing index: {index_name}")
            self.pc.delete_index(index_name)
            print(f"Index {index_name} deleted successfully")
        
        # Check if index exists, create if not
        if index_name not in self.pc.list_indexes().names():
            print(f"Creating new index: {index_name}")
            self.pc.create_index(
                name=index_name,
                spec=pinecone.ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                ),
                dimension=1536,
                metric="cosine"
            )
            print(f"Index {index_name} created successfully")
        
        self.index = self.pc.Index(index_name)

    def insert_index(self, vectors):
        try:
            self.index.upsert(vectors=vectors)
            return True
        except Exception as e:
            print(f"Error inserting vectors: {e}")
            return False

    def query(self, query_v, top_k=3, filter=None):
        return self.index.query(vector=query_v, top_k=top_k, filter=filter, include_metadata=True)
    
    def clear_index(self):
        """Clear all vectors from the index"""
        try:
            # Delete all vectors by using a filter that matches everything
            # This is a simple approach - we'll delete the index and recreate it
            index_name = self.index.name
            print(f"Deleting index: {index_name}")
            self.pc.delete_index(index_name)
            print(f"Recreating index: {index_name}")
            self.pc.create_index(
                name=index_name,
                spec=pinecone.ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                ),
                dimension=1536,
                metric="cosine"
            )
            self.index = self.pc.Index(index_name)
            print(f"Index {index_name} cleared and recreated successfully")
            return True
        except Exception as e:
            print(f"Error clearing index: {e}")
            return False
