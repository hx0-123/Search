"""
Secure Query URL Configuration
"""
from django.urls import path
from . import views

app_name = 'secure_query'

urlpatterns = [
    # ── Original APIs ────────────────────────────────────────
    path('initiate/',                views.initiate_query,    name='initiate_query'),
    path('update_location/',         views.update_location,   name='update_location'),
    path('<str:query_id>/result/',   views.get_query_result,  name='get_query_result'),

    # ── Query History (Task 1) ───────────────────────────────
    # GET /api/query/history/?page=1&page_size=10&status=completed
    path('history/',                 views.query_history,     name='query_history'),

    # ── Performance Statistics (Task 3) ─────────────────────
    # GET /api/query/stats/?days=7
    path('stats/',                   views.query_stats,       name='query_stats'),

    # ── Query Cancellation (Task 4) ─────────────────────────
    # DELETE /api/query/{query_id}/cancel/
    path('<str:query_id>/cancel/',   views.cancel_query,      name='cancel_query'),
]
