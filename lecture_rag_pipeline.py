import json
from typing import List
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI
from langchain_core.embeddings import Embeddings
import requests


class LMStudioEmbeddings(Embeddings):
    def __init__(self, endpoint_url: str = "http://localhost:1234/v1/embeddings", model_name: str = "text-embedding-nomic-embed-text-v1.5"):
        self.endpoint_url = endpoint_url
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        payload = {"model": self.model_name, "input": texts}
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.endpoint_url, json=payload, headers=headers)
        response.raise_for_status()
        return [item['embedding'] for item in response.json()["data"]]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]

class LectureRAGPipeline:
    def __init__(self, persist_dir: str = "chroma_db"):
        self.persist_dir = persist_dir

    def load_transcript(self, video_id: str) -> List[Document]:
        path = f"transcripts/{video_id}.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        docs = []
        for item in data:
            docs.append(Document(
                page_content=item["text"],
                metadata={
                    "video_id": item["video_id"],
                    "start": item["start"],
                    "end": item["end"]
                }
            ))
        return docs

    def chunk_documents(self, docs: List[Document], chunk_size: int = 700, overlap: int = 100) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        return splitter.split_documents(docs)

    def store_chunks(self, chunks: List[Document]):
        self.vectordb = Chroma.from_documents(
            chunks,
            embedding=LMStudioEmbeddings(),
            persist_directory=self.persist_dir
        )
        self.vectordb.persist()

    def load_vectorstore(self):
        self.vectordb = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=LMStudioEmbeddings()
        )

    def setup_qa_chain(self):
        if self.vectordb is None:
            self.load_vectorstore()

        retriever = self.vectordb.as_retriever(search_kwargs={"k": 3})

        llm = ChatOpenAI(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio",  # dummy key for local models
            model="google/gemma-3-4b",  # e.g., "mistralai/Mistral-7B-Instruct-v0.2"
            temperature=0.2
        )

        self.qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

    def query(self, question: str) -> str:
        if self.qa_chain is None:
            self.setup_qa_chain()
        return self.qa_chain.run(question)

    def run_pipeline(self, video_id: str):
        docs = self.load_transcript(video_id)
        chunks = self.chunk_documents(docs)
        self.store_chunks(chunks)
        self.setup_qa_chain()
