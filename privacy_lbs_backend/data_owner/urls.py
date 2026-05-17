"""
Data Owner URL Configuration
"""
from django.urls import path
from . import views

app_name = 'data_owner'

urlpatterns = [
    # ── Original Endpoints ──────────────────────────────────────
    path('upload/', views.upload_data, name='upload_data'),

    # ── Key Management ──────────────────────────────────────
    # GET  /api/data/keypair/   Query current active key status
    path('keypair/', views.get_keypair_status, name='get_keypair_status'),
    # POST /api/data/keygen/    Generate new key pair
    path('keygen/', views.generate_keypair, name='generate_keypair'),

    # ── Statistics ─────────────────────────────────────────
    # GET  /api/data/statistics/  POI total count, index status, etc.
    path('statistics/', views.get_statistics, name='get_statistics'),

    # ── Data Clear (Development/Test Only)────────────────────
    # POST /api/data/clear/   Clear all POI encrypted data
    path('clear/', views.clear_all_data, name='clear_all_data'),
]
