from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores import Pinecone as LangchainPinecone
from langchain.embeddings import OpenAIEmbeddings

from embeddings.embedder import Embedder
from database.PineconeDB import PCDB

from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")


class RAGRunner:

    def __init__(self, index_name, model_name="gpt-4.1-nano", temperature=0.3):
        self.index_name = index_name
        self.pcdb = PCDB(index_name=index_name)
        self.embedder = Embedder(pcdb_instance=self.pcdb)

        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        self.retriever = LangchainPinecone.from_existing_index(
            self.index_name, self.embeddings).as_retriever()

        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=OPENAI_API_KEY
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            return_source_documents=False
        )

    def ingest(self, text, category):
        vectors = self.embedder.embed_document(text, category=category)
        return self.pcdb.insert_index(vectors)

    def ask(self, question):
        return self.qa_chain.run(question)
