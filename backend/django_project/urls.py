from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin, if you ever need it
    path('admin/', admin.site.urls),

    # Your API endpoints live under /api/
    path('api/', include('notes.urls')),
]
