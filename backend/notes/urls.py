from django.urls import include, path
from rest_framework import routers

from .views import (
    ExtractViewSet,
    IngestViewSet,
    SearchViewSet,
    SummarizeAPIView,
    TabViewSet,
    UnitViewSet,
    NoteViewSet,
    QuestionViewSet,
)

router = routers.DefaultRouter()
router.register(r'extract', ExtractViewSet, basename='extract')
router.register(r'ingest',  IngestViewSet,  basename='ingest')
router.register(r'search',  SearchViewSet,  basename='search')
router.register(r'tabs', TabViewSet, basename='tab')
router.register(r'units', UnitViewSet, basename='unit')
router.register(r'notes', NoteViewSet, basename='note')
router.register(r'questions', QuestionViewSet, basename='question')

urlpatterns = [
    path('', include(router.urls)),
    path('summarize/', SummarizeAPIView.as_view(), name='summarize'),
]
