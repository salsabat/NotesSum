from rest_framework import serializers

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