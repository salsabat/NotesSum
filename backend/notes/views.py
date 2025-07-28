import os
from rest_framework.views import APIView
from rest_framework.renderers import BaseRenderer
from rest_framework import mixins, viewsets, status, permissions
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .serializers import (
    IngestRequestSerializer,
    IngestResponseSerializer,
    SearchRequestSerializer,
    SearchResponseSerializer,  
    SummarizeRequestSerializer, 
    SummarizeResponseSerializer,
)
from services.embedder import Embedder
from parsing.main import DocumentProcessor
from services.PineconeDB import PCDB
from openai import OpenAI

class PlainTextRenderer(BaseRenderer):
    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        # data is expected to be a string here
        if isinstance(data, str):
            return data.encode('utf-8')
        return str(data).encode('utf-8')


# initialize once
processor = DocumentProcessor()

pcdb = PCDB(index_name   = os.getenv("PINECONE_INDEX_NAME"))
embedder = Embedder(pcdb_instance=pcdb)
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ExtractViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    POST /api/extract/  → returns raw text/plain
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser]
    renderer_classes = [PlainTextRenderer]
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        pdf = request.FILES.get("file")
        if not pdf or not pdf.name.lower().endswith(".pdf"):
            return Response("Please upload a PDF.", status=status.HTTP_400_BAD_REQUEST)
        full_text = processor.process_pdf(pdf)["full_text"]
        return Response(full_text, status=status.HTTP_200_OK)

class IngestViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    POST /api/ingest/  → upserts embeddings into Pinecone
    """
    permission_classes = [permissions.AllowAny]
    serializer_class   = IngestRequestSerializer
    http_method_names  = ['post']

    def create(self, request, *args, **kwargs):
        ser = IngestRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        vectors = embedder.embed_document(
            data["text"],
            category=data["category"],
            chunk_size=data["chunk_size"],
            chunk_overlap=data["chunk_overlap"],
        )
        count = pcdb.upsert(vectors)

        out = {"success": True, "upserted": count}
        return Response(
            IngestResponseSerializer(out).data,
            status=status.HTTP_201_CREATED
        )

class SearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    GET /api/search/?query=…&top_k=…&category=…  → semantic search
    """
    permission_classes = [permissions.AllowAny]
    serializer_class   = SearchRequestSerializer
    http_method_names  = ['get']

    def list(self, request, *args, **kwargs):
        ser = SearchRequestSerializer(data=request.query_params)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        raw = embedder.search_texts_by_query(
            data["query"],
            top_k=data["top_k"],
            filter={"category": data.get("category")} if data.get("category") else None
        )
        matches = [
            {"id": m["id"], "score": m["score"], "snippet": m["metadata"]["text"]}
            for m in raw
        ]
        return Response(
            SearchResponseSerializer({"matches": matches}).data,
            status=status.HTTP_200_OK
        )

class SummarizeAPIView(APIView):
    """
    POST /api/summarize/
    {
      "question":"…",
      "namespace":"optional-namespace",
      "top_k":5
    }
    → returns JSON with an LLM‐generated answer + the raw context chunks used.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        #validate
        ser = SummarizeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        q, ns, top_k = (
            ser.validated_data["question"],
            ser.validated_data.get("namespace"),
            ser.validated_data["top_k"],
        )

        #retrieve top-K from Pinecone
        raw = embedder.search_texts_by_query(
            q,
            top_k=top_k,
            filter={"category": ns} if ns else None
        )
        context_chunks = [m["metadata"]["text"] for m in raw]

        #build prompt and call OpenAI
        prompt = (
            "You are a helpful assistant. Use the following context to answer the question:\n\n"
            + "\n\n---\n\n".join(context_chunks)
            + f"\n\nQuestion: {q}\nAnswer:"
        )
        chat_resp = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
        answer = chat_resp.choices[0].message.content.strip()

        #return
        out = {"answer": answer, "context": context_chunks}
        return Response(SummarizeResponseSerializer(out).data, status=status.HTTP_200_OK)