from rest_framework import serializers
from .models import Tab, Unit, Note, Question

class IngestRequestSerializer(serializers.Serializer):
    text          = serializers.CharField()
    category      = serializers.CharField()
    chunk_size    = serializers.IntegerField(default=500)
    chunk_overlap = serializers.IntegerField(default=50)

class IngestResponseSerializer(serializers.Serializer):
    success  = serializers.BooleanField()
    upserted = serializers.IntegerField()

class SearchRequestSerializer(serializers.Serializer):
    query    = serializers.CharField()
    top_k    = serializers.IntegerField(default=5)
    category = serializers.CharField(required=False, allow_blank=True)

class MatchSerializer(serializers.Serializer):
    id      = serializers.CharField()
    score   = serializers.FloatField()
    snippet = serializers.CharField()

class SearchResponseSerializer(serializers.Serializer):
    matches = MatchSerializer(many=True)

class SummarizeRequestSerializer(serializers.Serializer):
    question  = serializers.CharField()
    namespace = serializers.CharField(required=False, default=None)
    top_k     = serializers.IntegerField(required=False, default=5)

class SummarizeResponseSerializer(serializers.Serializer):
    answer  = serializers.CharField()
    context = serializers.ListField(child=serializers.CharField())

class TabSerializer(serializers.ModelSerializer):
    units_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tab
        fields = ['id', 'name', 'color', 'units_count']
    
    def get_units_count(self, obj):
        return obj.units.count()

class UnitSerializer(serializers.ModelSerializer):
    notes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = ['id', 'tab', 'name', 'description', 'order', 'notes_count', 'created_at']
    
    def get_notes_count(self, obj):
        return obj.notes.count()

class NoteSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    
    class Meta:
        model = Note
        fields = ['id', 'unit', 'unit_name', 'title', 'content', 'summary', 'file', 'extraction_method', 'created_at']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'note', 'question', 'answer', 'timestamp']
