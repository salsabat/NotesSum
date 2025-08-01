import os
import uuid
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class Embedder:

    def __init__(self, pcdb_instance, chunk_size=500, chunk_overlap=50):
        self.embedder = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", "!", "?", " "]
        )
        self.pcdb = pcdb_instance
    # put class name as category
    def embed_document(self, text, category):
        chunks = self.text_splitter.split_text(text)
        vectors = self.embedder.embed_documents(chunks)
        pinecone_vectors = []

        for vec, chunk in zip(vectors, chunks):
            vector_id = str(uuid.uuid4())
            pinecone_vectors.append({
                "id": vector_id,
                "values": vec,
                "metadata": {
                    "text": chunk,
                    "category": category
                }
            })

        return pinecone_vectors

    # query is just text
    def embed_query(self, query):
        return self.embedder.embed_query(query)

    def search_texts_by_query(self, query, top_k=5, filter=None):
        query_vector = self.embed_query(query)
        results = self.pcdb.query(query_vector, top_k=top_k, filter=filter)
        return results
