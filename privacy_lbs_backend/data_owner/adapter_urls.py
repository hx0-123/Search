from django.urls import path
from . import views

urlpatterns = [
    # POST /api/data_owner/upload/      CSV file upload (multipart/form-data)
    path('upload/', views.upload_csv, name='upload_csv'),

    # GET  /api/data_owner/statistics/  Data statistics (total POIs, index status, key status)
    path('statistics/', views.get_statistics, name='adapter_get_statistics'),

    # GET  /api/data_owner/keypair/     Key pair status (same as /api/data/keypair/)
    path('keypair/', views.get_keypair_status, name='adapter_get_keypair_status'),
]
