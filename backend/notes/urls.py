# notes/urls.py

from django.urls import include, path
from rest_framework import routers

from .views import (
    ExtractViewSet,
    IngestViewSet,
    SearchViewSet,
    SummarizeAPIView,     
)

router = routers.DefaultRouter()
router.register(r'extract', ExtractViewSet, basename='extract')
router.register(r'ingest',  IngestViewSet,  basename='ingest')
router.register(r'search',  SearchViewSet,  basename='search')

urlpatterns = [
    path('', include(router.urls)),
    path('summarize/', SummarizeAPIView.as_view(), name='summarize'),
]
