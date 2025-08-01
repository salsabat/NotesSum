import os
import tempfile
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.renderers import BaseRenderer
from rest_framework import mixins, viewsets, status, permissions, renderers
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.db import models

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


processor = DocumentProcessor()

pcdb = PCDB(index_name="notes-summarizer-v2", force_recreate=True)
embedder = Embedder(pcdb_instance=pcdb)
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ExtractViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    POST /api/extract/  → returns JSON with text and extraction method
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser]
    renderer_classes = [renderers.JSONRenderer]  # Changed to JSON renderer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        pdf = request.FILES.get("file")
        if not pdf or not pdf.name.lower().endswith(".pdf"):
            return Response({"error": "Please upload a PDF."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Save the uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                for chunk in pdf.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Process the PDF using the temporary file path
                print(f"Processing PDF: {temp_file_path}")
                results = processor.process_pdf(Path(temp_file_path))
                print(f"Processing results: {results}")
                
                # Extract text from all pages
                full_text = ""
                extraction_method = "OCR"
                
                # Check if this was fast extraction (PyMuPDF)
                if results.get('pages') and len(results['pages']) == 1:
                    page = results['pages'][0]
                    if page.get('regions') and len(page['regions']) == 1:
                        region = page['regions'][0]
                        if region.get('extractor') == 'PyMuPDF':
                            extraction_method = "Text Layer (Fast)"
                
                for page in results.get('pages', []):
                    print(f"Processing page: {page}")
                    for region in page.get('regions', []):
                        print(f"Processing region: {region}")
                        if region.get('type') == 'text' and region.get('content'):
                            full_text += region.get('content', '') + "\n"
                
                print(f"Extracted text length: {len(full_text)}")
                print(f"Extraction method: {extraction_method}")
                
                return Response({
                    "text": full_text,
                    "extraction_method": extraction_method,
                    "filename": pdf.name
                }, status=status.HTTP_200_OK)
            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            return Response({"error": f"Error processing PDF: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

        print(f"Ingesting text with category: {data['category']}")
        print(f"Text length: {len(data['text'])} characters")

        vectors = embedder.embed_document(
            data["text"],
            category=data["category"]
        )
        
        print(f"Created {len(vectors)} vectors for category: {data['category']}")
        
        success = pcdb.insert_index(vectors)
        count = len(vectors) if success else 0

        print(f"Successfully inserted {count} vectors into Pinecone")

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
        ser = SummarizeRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        q, ns, top_k = (
            ser.validated_data["question"],
            ser.validated_data.get("namespace"),
            ser.validated_data["top_k"],
        )

        print(f"Searching for question: '{q}' with namespace: '{ns}' and top_k: {top_k}")

        try:
            filter_dict = {"category": ns} if ns else None
            print(f"Using filter: {filter_dict}")
            
            raw = embedder.search_texts_by_query(
                q,
                top_k=top_k,
                filter=filter_dict
            )
            print(f"Pinecone query result: {raw}")
            print(f"Result type: {type(raw)}")
            print(f"Result has matches: {hasattr(raw, 'matches')}")
            if hasattr(raw, 'matches'):
                print(f"Number of matches: {len(raw.matches)}")
            
            if not raw or (hasattr(raw, 'matches') and len(raw.matches) == 0):
                print("No results found in Pinecone")
                return Response({
                    "answer": "I couldn't find any relevant information in the uploaded document to answer your question. Please make sure the document has been properly uploaded and contains relevant content.",
                    "context": []
                }, status=status.HTTP_200_OK)
            
            context_chunks = []
            
            if hasattr(raw, 'matches'):
                for match in raw.matches:
                    try:
                        if hasattr(match, 'metadata') and hasattr(match.metadata, 'text'):
                            context_chunks.append(match.metadata.text)
                        elif isinstance(match.metadata, dict) and 'text' in match.metadata:
                            context_chunks.append(match.metadata['text'])
                        else:
                            print(f"Unexpected match format: {match}")
                    except Exception as e:
                        print(f"Error processing match: {e}")
                        continue
            else:
                for m in raw:
                    try:
                        if hasattr(m, 'metadata') and hasattr(m.metadata, 'text'):
                            context_chunks.append(m.metadata.text)
                        elif isinstance(m, dict) and 'metadata' in m and 'text' in m['metadata']:
                            context_chunks.append(m['metadata']['text'])
                        else:
                            print(f"Unexpected result format: {m}")
                    except Exception as e:
                        print(f"Error processing result item: {e}")
                        continue
            
            print(f"Extracted {len(context_chunks)} context chunks")
            
        except Exception as e:
            print(f"Pinecone query error: {e}")
            return Response({
                "answer": "I encountered an error while searching the document. Please try again.",
                "context": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not context_chunks:
            return Response({
                "answer": "I couldn't find any relevant information in the uploaded document to answer your question.",
                "context": []
            }, status=status.HTTP_200_OK)

        prompt = (
            "Use the following context to answer the question:\n\n"
            + "\n\n---\n\n".join(context_chunks)
            + f"\n\nQuestion: {q}\nAnswer:"
        )
        
        try:
            chat_resp = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
            )
            answer = chat_resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return Response({
                "answer": "I encountered an error while generating the answer. Please try again.",
                "context": context_chunks
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        #return
        out = {"answer": answer, "context": context_chunks}
        return Response(SummarizeResponseSerializer(out).data, status=status.HTTP_200_OK)


# New ViewSets for Tabs/Units/Notes/Questions
from .models import Tab, Unit, Note, Question
from .serializers import TabSerializer, UnitSerializer, NoteSerializer, QuestionSerializer

class TabViewSet(viewsets.ModelViewSet):
    serializer_class = TabSerializer
    permission_classes = [permissions.AllowAny] # Temporarily allow any for testing

    def get_queryset(self):
        return Tab.objects.all() # Temporarily return all tabs

    def perform_create(self, serializer):
        from django.contrib.auth.models import User
        try:
            user = User.objects.first()
            if not user:
                user = User.objects.create_user(
                    username='default_user',
                    email='default@example.com',
                    password='defaultpass123'
                )
        except Exception as e:
            print(f"Error creating default user: {e}")
            user = User.objects.first() # Fallback
        serializer.save(user=user)

    def destroy(self, request, *args, **kwargs):
        """Delete a tab and all its associated units and notes"""
        tab = self.get_object()
        
        # Delete all notes associated with units in this tab
        for unit in tab.units.all():
            unit.notes.all().delete()
        
        # Delete all units in this tab
        tab.units.all().delete()
        
        # Delete the tab itself
        tab.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow any for testing

    def get_queryset(self):
        tab_id = self.request.query_params.get('tab', None)
        
        # For list operations (GET), filter by tab if specified
        if self.action == 'list':
            if tab_id:
                return Unit.objects.filter(tab_id=tab_id)
            else:
                return Unit.objects.none()
        
        # For individual operations (GET/PUT/DELETE by ID), return all units
        # The URL contains the unit ID, so we can access any unit
        return Unit.objects.all()

    def perform_create(self, serializer):
        # Set the order to be the next available order for this tab
        tab = serializer.validated_data['tab']
        max_order = Unit.objects.filter(tab=tab).aggregate(
            models.Max('order')
        )['order__max'] or -1
        serializer.save(order=max_order + 1)

    def destroy(self, request, *args, **kwargs):
        """Delete a unit and all its associated notes"""
        unit = self.get_object()
        
        # Delete all notes associated with this unit
        unit.notes.all().delete()
        
        # Delete the unit itself
        unit.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow any for testing

    def get_queryset(self):
        unit_id = self.request.query_params.get('unit', None)
        tab_id = self.request.query_params.get('tab', None)
        
        # For list operations (GET), filter appropriately
        if self.action == 'list':
            if unit_id:
                return Note.objects.filter(unit_id=unit_id)
            elif tab_id:
                return Note.objects.filter(unit__tab_id=tab_id)
            else:
                return Note.objects.filter(unit__isnull=False)
        
        # For individual operations (GET/PUT/DELETE by ID), return all notes
        return Note.objects.all()

    def perform_create(self, serializer):
        serializer.save()

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Question.objects.filter(note__unit__tab__user=self.request.user)
