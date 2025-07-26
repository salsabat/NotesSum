import os
from dotenv import load_dotenv
from PineconeDB import PCDB
from embedder import Embedder
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain import hub


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")


class RAGRunner:
    def __init__(self, index_name, model_name="gpt-4.1-nano", temperature=0.3):
        self.index_name = index_name

        self.pcdb = PCDB(index_name=index_name)
        self.embedder = Embedder(pcdb_instance=self.pcdb)

        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            openai_api_key=OPENAI_API_KEY
        )
        self.retrieval_qa_chat_prompt = hub.pull(
            "langchain-ai/retrieval-qa-chat")
        self.combine_chain = create_stuff_documents_chain(
            llm=self.llm, prompt=self.retrieval_qa_chat_prompt)

    def ingest(self, text, category):
        vectors = self.embedder.embed_document(text, category=category)
        return self.pcdb.insert_index(vectors)

    def ask(self, question, top_k=10, category=None):
        if category:
            texts = self.embedder.search_texts_by_query(
                query=question, top_k=top_k, filter={'category': category})
        else:
            texts = self.embedder.search_texts_by_query(
                query=question, top_k=top_k)

        matches = texts.get('matches', [])
        docs = [
            Document(page_content=match['metadata']
                     ['text'], metadata=match['metadata'])
            for match in matches
        ]

        response = self.combine_chain.invoke({
            "input": question,
            "context": docs
        })

        return response['answer']
