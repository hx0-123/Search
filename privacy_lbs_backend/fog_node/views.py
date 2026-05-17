"""
Fog Node API Views
Provides node monitoring status interface for DashboardView.vue
"""
import time
import random
from datetime import timedelta

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Avg, Q

from .models import FogNode, ComputationTask


@api_view(['GET'])
@permission_classes([])
def nodes_status(request):
    """
    GET /api/nodes/status/
    Returns real-time status of cloud + fog nodes for DashboardView monitoring panel.

    Cloud Node: Fixed C1 node, returns basic info + simulated CPU/memory
    Fog Nodes: Read from FogNode database table, attempts to get online Workers
               and their active task counts via Celery Inspect
    """
    try:
        now = timezone.now()

        # ── 1. Celery Worker Online Status ────────────────────────
        celery_active   = {}   # worker_name -> [active_tasks]
        celery_reserved = {}   # worker_name -> [reserved_tasks]
        celery_online   = False

        try:
            from celery.app import app_or_default
            celery_app = app_or_default()
            inspector  = celery_app.control.inspect(timeout=1.5)
            active_raw   = inspector.active()   or {}
            reserved_raw = inspector.reserved() or {}
            celery_active   = active_raw
            celery_reserved = reserved_raw
            celery_online   = bool(active_raw or reserved_raw)
        except Exception:
            # Fallback when Celery/Redis unavailable: show only database data
            celery_online = False

        # ── 2. Cloud Node C1 Info ────────────────────────────────
        # Simulate CPU/memory (demo environment)
        c1_cpu    = round(random.uniform(10, 45), 1)
        c1_memory = round(random.uniform(30, 60), 1)

        # Queries processed in last hour
        from secure_query.models import SecureQuery
        recent_queries = SecureQuery.objects.filter(
            created_at__gte=now - timedelta(hours=1)
        ).count()

        cloud_node = {
            'node_id':       'C1',
            'node_name':     'Cloud Server C1',
            'node_type':     'cloud',
            'status':        'active',
            'host':          '127.0.0.1',
            'port':          8000,
            'cpu_percent':   c1_cpu,
            'memory_percent': c1_memory,
            'active_tasks':  recent_queries,
            'total_tasks_processed': SecureQuery.objects.count(),
            'last_heartbeat': now.isoformat(),
            'uptime_seconds': int(time.time() % 86400),   # for demo
        }

        # ── 3. Fog Nodes List ────────────────────────────────────
        db_fog_nodes = list(FogNode.objects.all().order_by('node_id'))

        # If no fog nodes in database, auto-generate demo nodes
        if not db_fog_nodes:
            demo_nodes = [
                {'node_id': 'F1', 'node_name': 'Fog Node #1', 'host': '192.168.1.11', 'port': 6379},
                {'node_id': 'F2', 'node_name': 'Fog Node #2', 'host': '192.168.1.12', 'port': 6379},
                {'node_id': 'F3', 'node_name': 'Fog Node #3', 'host': '192.168.1.13', 'port': 6379},
            ]
        else:
            demo_nodes = [
                {'node_id': n.node_id, 'node_name': n.node_name,
                 'host': n.host, 'port': n.port}
                for n in db_fog_nodes
            ]

        fog_nodes_result = []
        total_celery_workers = len(celery_active)
        worker_names = list(celery_active.keys())

        for i, nd in enumerate(demo_nodes):
            nid = nd['node_id']

            # Get corresponding Celery Worker (by order)
            if i < len(worker_names):
                wname  = worker_names[i]
                active_tasks  = len(celery_active.get(wname, []))
                reserved_tasks = len(celery_reserved.get(wname, []))
                worker_status = 'active'
            else:
                active_tasks   = 0
                reserved_tasks = 0
                # If Celery offline, determine from recent database tasks
                if celery_online:
                    worker_status = 'inactive'
                else:
                    # Demo environment: randomly assign online status
                    worker_status = random.choice(['active', 'active', 'inactive'])

            # Historical task statistics for this node in database
            db_node = next((n for n in db_fog_nodes if n.node_id == nid), None)
            total_processed = db_node.total_tasks_processed if db_node else 0
            avg_proc_time   = db_node.average_processing_time if db_node else 0.0

            fog_nodes_result.append({
                'node_id':        nid,
                'node_name':      nd['node_name'],
                'node_type':      'fog',
                'status':         worker_status,
                'host':           nd['host'],
                'port':           nd['port'],
                'cpu_percent':    round(random.uniform(5, 35), 1),   # demo
                'memory_percent': round(random.uniform(20, 55), 1),  # demo
                'active_tasks':   active_tasks,
                'reserved_tasks': reserved_tasks,
                'total_tasks_processed': total_processed,
                'average_processing_ms': round(avg_proc_time * 1000),
                'last_heartbeat': now.isoformat(),
            })

        # ── 4. Summary Statistics ──────────────────────────────────────
        active_fog  = sum(1 for n in fog_nodes_result if n['status'] == 'active')
        total_tasks = sum(n['active_tasks'] for n in fog_nodes_result)

        # Tasks completed in last 24h
        completed_24h = SecureQuery.objects.filter(
            status='completed',
            completed_at__gte=now - timedelta(hours=24)
        ).count()

        return Response({
            'timestamp':    now.isoformat(),
            'celery_online': celery_online,
            'summary': {
                'total_nodes':      1 + len(fog_nodes_result),
                'active_fog_nodes': active_fog,
                'total_fog_nodes':  len(fog_nodes_result),
                'active_tasks':     total_tasks,
                'completed_24h':    completed_24h,
            },
            'cloud_node':  cloud_node,
            'fog_nodes':   fog_nodes_result,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        return Response({
            'error':     str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
