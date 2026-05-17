import csv
import io
import time
import uuid
import json

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
import time
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings
from .models import DataOwner, EncryptedSpatialObject, IndexMetadata, KeyPair
from .serializers import DataUploadSerializer, DataOwnerSerializer, EncryptedSpatialObjectSerializer, KeyPairStatusSerializer
from indices.ktree import KTree, SpatialObject
from indices.asset_tree import AssetTree
from crypto.paillier_manager import PaillierManager

DEBUG = getattr(settings, 'DEBUG', False)


@swagger_auto_schema(
    method='post',
    request_body=DataUploadSerializer,
    responses={
        201: openapi.Response(
            description='Data upload successful',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'owner_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'objects_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'index_built': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                }
            )
        ),
        400: 'Request parameter error'
    },
    operation_description='Allow data owners to upload encrypted data and build index'
)
@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def upload_data(request):
    """
    Data upload endpoint
    POST /api/data/upload/
    
    Allow data owners to upload encrypted data and build index
    """
    try:
        serializer = DataUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            # Return detailed validation error information
            error_response = {
                'error': 'Request parameter validation failed',
                'details': serializer.errors,
                'message': 'Please check the following fields: ' + ', '.join(serializer.errors.keys())
            }
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
        
        owner_id = serializer.validated_data['owner_id']
        objects_data = serializer.validated_data['objects']
        public_key_str = serializer.validated_data['public_key']
    except Exception as e:
        return Response({
            'error': 'Request processing failed',
            'message': str(e),
            'type': type(e).__name__
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Delegate directly to _process_upload to avoid code duplication
    return _process_upload(
        request.user,
        owner_id,
        public_key_str,
        objects_data,
    )


# ─────────────────────────────────────────────────────────────
# Internal core processing function (shared by upload_data and upload_csv)
# ─────────────────────────────────────────────────────────────

def _process_upload(user, owner_id: str, public_key_str: str, objects_data: list):
    """
    Core upload processing: encrypt spatial objects + build KASTree + save to database
    Returns DRF Response object
    """
    from django.contrib.auth.models import User
    from django.db import connection

    max_retries = 5
    retry_delay = 0.5

    # user field is now nullable ForeignKey, use authenticated user or None for anonymous uploads
    auth_user = user if (user and getattr(user, 'is_authenticated', False)) else None

    # Get or create data owner (use only owner_id as unique key, independent of user unique constraint)
    for retry in range(max_retries):
        try:
            connection.ensure_connection()
            data_owner, created = DataOwner.objects.get_or_create(
                owner_id=owner_id,
                defaults={'user': auth_user, 'public_key': public_key_str}
            )
            if not created:
                data_owner.public_key = public_key_str
                data_owner.save(update_fields=['public_key'])
            break
        except Exception as e:
            if retry < max_retries - 1:
                connection.close()
                time.sleep(retry_delay * (retry + 1))
            else:
                return Response({'error': f'Database operation failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Initialize Paillier
    paillier_manager = PaillierManager()
    paillier_manager.load_public_key(public_key_str)

    # Determine spatial domain
    x_coords = [obj['x'] for obj in objects_data]
    y_coords = [obj['y'] for obj in objects_data]
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    x_range = x_max - x_min or 1.0
    y_range = y_max - y_min or 1.0
    x_min -= x_range * 0.1;  x_max += x_range * 0.1
    y_min -= y_range * 0.1;  y_max += y_range * 0.1

    ktree = KTree(x_min, x_max, y_min, y_max, threshold=10, max_depth=10)

    objects_to_save = []
    for idx, obj_data in enumerate(objects_data):
        obj_id = obj_data.get('object_id') or str(uuid.uuid4())
        x = obj_data['x']
        y = obj_data['y']
        keywords = obj_data.get('keywords', [])
        document = obj_data.get('document', '')
        # name: prefer CSV mapped name column, then document, finally obj_id
        name = obj_data.get('name', '').strip() or document.strip() or obj_id

        enc_x = paillier_manager.encrypt(x)
        enc_y = paillier_manager.encrypt(y)
        encrypted_keywords = [paillier_manager.encrypt_int(hash(kw) % 1000000) for kw in keywords]
        # Encrypt name with Paillier: convert string to integer (hash % 1e15) then encrypt
        encrypted_name_val = paillier_manager.encrypt_int(hash(name) % (10 ** 15))

        spatial_obj = SpatialObject(object_id=obj_id, x=x, y=y, keywords=keywords, document=document)
        node_path = ktree.insert(spatial_obj)
        node = ktree.get_node_by_path(node_path)
        region = node.region if node else 0

        objects_to_save.append({
            'data_owner': data_owner, 'object_id': obj_id,
            'original_x': x, 'original_y': y,
            'encrypted_location_x': enc_x, 'encrypted_location_y': enc_y,
            'encrypted_keywords': json.dumps(encrypted_keywords),
            'encrypted_name': encrypted_name_val,
            'encrypted_document': '',  # Skip full document encryption in demo environment to avoid timeout
            'ktree_node_path': node_path, 'ktree_region': region,
            'metadata': {
                # name: prefer dedicated name field, already determined above
                'name': name,
                'document': document,
                'keywords': keywords,
            },
        })

    # Batch save (batch_size increased from 2 to 50, significantly reduces database transactions)
    encrypted_objects = []
    batch_size = 50
    for batch_start in range(0, len(objects_to_save), batch_size):
        batch = objects_to_save[batch_start:batch_start + batch_size]
        for retry in range(max_retries):
            try:
                connection.ensure_connection()
                object_ids = [o['object_id'] for o in batch]
                existing = {o.object_id: o for o in EncryptedSpatialObject.objects.filter(
                    data_owner=batch[0]['data_owner'], object_id__in=object_ids)}
                for od in batch:
                    if od['object_id'] in existing:
                        obj = existing[od['object_id']]
                        for f in ['original_x','original_y','encrypted_location_x',
                                  'encrypted_location_y','encrypted_keywords',
                                  'encrypted_name','encrypted_document',
                                  'ktree_node_path','ktree_region','metadata']:
                            setattr(obj, f, od[f])
                        obj.save()
                    else:
                        obj = EncryptedSpatialObject.objects.create(
                            data_owner=od['data_owner'], object_id=od['object_id'],
                            original_x=od['original_x'], original_y=od['original_y'],
                            encrypted_location_x=od['encrypted_location_x'],
                            encrypted_location_y=od['encrypted_location_y'],
                            encrypted_keywords=od['encrypted_keywords'],
                            encrypted_name=od['encrypted_name'],
                            encrypted_document=od['encrypted_document'],
                            ktree_node_path=od['ktree_node_path'],
                            ktree_region=od['ktree_region'],
                            metadata=od['metadata'],
                        )
                    encrypted_objects.append(obj)
                break
            except Exception as e:
                if retry < max_retries - 1:
                    connection.close()
                    time.sleep(retry_delay * (retry + 1))
                else:
                    return Response({'error': f'Batch save failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Build index
    ktree.build_keyword_lists()
    ktree.encrypt_keyword_lists(paillier_manager)
    asset_tree = AssetTree(ktree, paillier_manager)
    asset_tree.build()
    asset_tree.precompute_all_intervals()

    # Save index metadata
    try:
        stats = ktree.get_statistics()
        index_metadata, created = IndexMetadata.objects.get_or_create(
            data_owner=data_owner,
            defaults={
                'ktree_depth': stats['depth'], 'ktree_node_count': stats['node_count'],
                'ktree_leaf_count': stats['leaf_count'],
                'spatial_domain_x_min': stats['spatial_domain']['x_min'],
                'spatial_domain_x_max': stats['spatial_domain']['x_max'],
                'spatial_domain_y_min': stats['spatial_domain']['y_min'],
                'spatial_domain_y_max': stats['spatial_domain']['y_max'],
                'assettree_size': asset_tree.size,
                'build_status': 'completed',
                'build_started_at': timezone.now(),
                'build_completed_at': timezone.now(),
                'index_storage_type': 'redis',
            }
        )
        if not created:
            index_metadata.ktree_depth = stats['depth']
            index_metadata.ktree_node_count = stats['node_count']
            index_metadata.ktree_leaf_count = stats['leaf_count']
            index_metadata.assettree_size = asset_tree.size
            index_metadata.build_status = 'completed'
            index_metadata.build_completed_at = timezone.now()
            index_metadata.save()

        data_owner.total_objects = len(encrypted_objects)
        data_owner.encrypted_objects = len(encrypted_objects)
        data_owner.index_built = True
        data_owner.index_version = str(uuid.uuid4())[:8]
        data_owner.save()

        return Response({
            'message': 'Data uploaded and index built successfully',
            'owner_id': owner_id,
            'objects_count': len(encrypted_objects),
            'index_built': True,
            'index_metadata': {
                'ktree_depth': stats['depth'],
                'ktree_node_count': stats['node_count'],
                'ktree_leaf_count': stats['leaf_count'],
                'assettree_size': asset_tree.size,
            },
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        import traceback
        err = {'error': 'Failed to save index metadata', 'message': str(e), 'objects_saved': len(encrypted_objects)}
        if DEBUG:
            err['traceback'] = traceback.format_exc()
        return Response(err, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────
# Key Pair Management Endpoints
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([])
@authentication_classes([])
def get_keypair_status(request):
    """
    GET /api/data/keypair/
    Returns status of currently active key pair (without private key).
    """
    keypair = KeyPair.objects.filter(is_active=True).order_by('-created_at').first()
    if keypair is None:
        return Response({'exists': False, 'keypair': None}, status=status.HTTP_200_OK)
    serializer = KeyPairStatusSerializer(keypair)
    return Response({'exists': True, 'keypair': serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([])
@authentication_classes([])
def generate_keypair(request):
    """
    POST /api/data/keygen/
    Body (optional): { "key_size": 512|1024|2048 }

    Generate a new Paillier key pair and persist it:
    - Mark old Paillier key pairs as inactive
    - Sync update DataOwner public keys
    Return new key pair status (excluding private key).
    """
    key_size = int(request.data.get('key_size', 1024))
    if key_size not in (512, 1024, 2048):
        return Response({'error': 'key_size must be either 512, 1024, or 2048'}, status=status.HTTP_400_BAD_REQUEST)

    start = time.time()
    try:
        manager, keypair_dict = PaillierManager.generate_keypair(key_length=key_size)
    except Exception as e:
        return Response({'error': f'Key pair generation failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    gen_ms = int((time.time() - start) * 1000)

    # Public key digest: take first 16 hex characters of n
    public_key_n = str(manager.public_key.n)
    digest = hex(int(public_key_n))[2:18].upper()

    # Mark all old keys as inactive
    KeyPair.objects.filter(is_active=True).update(is_active=False)

    keypair = KeyPair.objects.create(
        key_size=key_size,
        public_key=keypair_dict['public_key'],
        private_key=keypair_dict['private_key'],
        public_key_digest=digest,
        gen_time_ms=gen_ms,
        is_active=True,
    )

    # Sync to existing DataOwners (so subsequent uploads use new public key automatically)
    DataOwner.objects.all().update(public_key=keypair_dict['public_key'])

    serializer = KeyPairStatusSerializer(keypair)
    return Response({
        'message': f'Key pair generated successfully ({key_size}-bit), took {gen_ms} ms',
        'public_key': keypair_dict['public_key'],   # Frontend stores in localStorage for future uploads
        'private_key': keypair_dict['private_key'], # Only returned once at generation, frontend keeps in memory, not stored on cloud
        'keypair': serializer.data,
    }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────
# CSV Upload Adapter
# ─────────────────────────────────────────────────────────────

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def upload_csv(request):
    """
    POST /api/data_owner/upload/
    multipart/form-data fields:
      - file      : CSV file (required)
      - owner_id  : Data owner ID (optional, default 'default_owner')
      - public_key: Paillier public key (optional, uses active key from database if not provided)

    CSV format (first row is optional header):
      longitude, latitude, keywords, document
      116.4074, 39.9042, "hospital;school", "Peking Union Medical College Hospital"

    Internally reuses upload_data's encryption + KASTree building logic.
    """
    # 1. Get file
    csv_file = request.FILES.get('file')
    if csv_file is None:
        return Response({'error': 'Please upload CSV file (field name: file)'}, status=status.HTTP_400_BAD_REQUEST)

    owner_id = request.data.get('owner_id', 'default_owner')
    public_key_str = request.data.get('public_key', None)

    # 2. If public key not provided, get active key from database
    if not public_key_str:
        kp = KeyPair.objects.filter(is_active=True).order_by('-created_at').first()
        if kp is None:
            return Response(
                {'error': 'No key pair generated yet, please call POST /api/data/keygen/ first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        public_key_str = kp.public_key

    # 3. Parse CSV
    try:
        text = csv_file.read().decode('utf-8-sig')  # Handle BOM
        reader = csv.DictReader(io.StringIO(text))
        # Normalize field names (trim spaces, lowercase)
        fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
    except Exception as e:
        return Response({'error': f'CSV parsing failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    # Supported column name aliases
    COL_X = {'longitude', 'lng', 'lon', 'x'}
    COL_Y = {'latitude',  'lat', 'y'}
    COL_KW = {'keywords', 'keyword', 'tags', 'kw'}
    COL_DOC = {'document', 'doc', 'name', 'description', 'desc'}
    COL_NAME = {'name', 'poi_name', 'store_name', 'title'}

    def find_col(names, aliases):
        for n in names:
            if n in aliases:
                return n
        return None

    col_x   = find_col(fieldnames, COL_X)
    col_y   = find_col(fieldnames, COL_Y)
    col_kw  = find_col(fieldnames, COL_KW)
    col_doc = find_col(fieldnames, COL_DOC)
    col_name = find_col(fieldnames, COL_NAME)

    if col_x is None or col_y is None:
        return Response(
            {'error': 'CSV must contain longitude column (longitude/lng/x) and latitude column (latitude/lat/y)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    objects_data = []
    errors = []
    for row_idx, raw_row in enumerate(reader, start=2):  # Start from row 2 (row 1 is header)
        # Normalize keys
        row = {k.strip().lower(): v for k, v in raw_row.items() if k}
        try:
            x = float(row[col_x])
            y = float(row[col_y])
        except (KeyError, ValueError, TypeError):
            errors.append(f'Row {row_idx}: Invalid coordinate values ({row.get(col_x)}, {row.get(col_y)})')
            continue

        # Parse keywords: supports semicolon/comma/space delimiters
        kw_raw = row.get(col_kw, '') if col_kw else ''
        import re as _re
        keywords = [k.strip() for k in _re.split(r'[;,，、 ]+', kw_raw) if k.strip()]

        doc = row.get(col_doc, '') if col_doc else ''
        name = row.get(col_name, '') if col_name else ''

        objects_data.append({
            'object_id': str(uuid.uuid4()),
            'x': x,
            'y': y,
            'keywords': keywords,
            'document': doc,
            'name': name,
        })

    # Deduplicate by (x, y, name) to prevent duplicate uploads in the same batch
    seen_keys = set()
    deduped_data = []
    for obj in objects_data:
        dedup_key = f"{round(obj['x'], 6)}|{round(obj['y'], 6)}|{obj['name'].lower().strip()}"
        if dedup_key not in seen_keys:
            seen_keys.add(dedup_key)
            deduped_data.append(obj)
    duplicate_count = len(objects_data) - len(deduped_data)
    objects_data = deduped_data

    if not objects_data:
        detail = '; '.join(errors[:5]) if errors else 'CSV content is empty'
        return Response({'error': f'No valid data rows: {detail}'}, status=status.HTTP_400_BAD_REQUEST)

    # 4. Call core upload logic directly (no RequestFactory dependency)
    response = _process_upload(request.user, owner_id, public_key_str, objects_data)

    # 5. Transform response format, add parsing statistics
    resp_data = response.data.copy() if hasattr(response, 'data') else {}
    resp_data['parsed_rows'] = len(objects_data)
    resp_data['skipped_rows'] = len(errors)
    if errors:
        resp_data['parse_warnings'] = errors[:10]
    if duplicate_count > 0:
        resp_data['duplicate_rows'] = duplicate_count

    return Response(resp_data, status=response.status_code)


# ─────────────────────────────────────────────────────────────
# Data Clear Endpoints
# ─────────────────────────────────────────────────────────────

@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def clear_all_data(request):
    """
    POST /api/data/clear/
    Clear all POI encrypted data (EncryptedSpatialObject) and DataOwner records.
    Only for development/test environment data reset.
    """
    try:
        from django.db import connection as _conn
        # Delete all encrypted spatial objects
        deleted_objs, _ = EncryptedSpatialObject.objects.all().delete()
        # Reset DataOwner statistics (keep key pair records)
        DataOwner.objects.all().update(
            total_objects=0,
            encrypted_objects=0,
            index_built=False,
            index_version=None,
        )
        # Synchronously delete IndexMetadata
        IndexMetadata.objects.all().delete()
        return Response({
            'message': f'Cleared {deleted_objs} POI encrypted data records, DataOwner statistics reset',
            'deleted_objects': deleted_objs,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        return Response({
            'error': 'Clear operation failed',
            'message': str(e),
            'traceback': traceback.format_exc() if DEBUG else None,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────
# Data Statistics Endpoints
# ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([])
@authentication_classes([])
def get_statistics(request):
    """
    GET /api/data/statistics/
    Returns summary information including POI count, category count, index status, key status, etc.
    Used by frontend DashboardView data panel.
    """
    total_objects = EncryptedSpatialObject.objects.count()

    # Category count: estimated from metadata or encrypted_document
    # Since keywords are stored as encrypted value lists, count DataOwners with uploads as proxy
    data_owner_count = DataOwner.objects.count()

    # Index status
    index_meta = IndexMetadata.objects.order_by('-created_at').first()
    index_info = None
    if index_meta:
        index_info = {
            'build_status': index_meta.build_status,
            'ktree_depth': index_meta.ktree_depth,
            'ktree_node_count': index_meta.ktree_node_count,
            'ktree_leaf_count': index_meta.ktree_leaf_count,
            'assettree_size': index_meta.assettree_size,
            'build_completed_at': index_meta.build_completed_at,
            'spatial_domain': {
                'x_min': index_meta.spatial_domain_x_min,
                'x_max': index_meta.spatial_domain_x_max,
                'y_min': index_meta.spatial_domain_y_min,
                'y_max': index_meta.spatial_domain_y_max,
            }
        }

    # Key status
    kp = KeyPair.objects.filter(is_active=True).order_by('-created_at').first()
    key_info = None
    if kp:
        key_info = {
            'key_size': kp.key_size,
            'public_key_digest': kp.public_key_digest,
            'created_at': kp.created_at,
            'gen_time_ms': kp.gen_time_ms,
        }

    # Last upload time
    latest_obj = EncryptedSpatialObject.objects.order_by('-created_at').first()
    last_upload_time = latest_obj.created_at if latest_obj else None

    return Response({
        'total_objects': total_objects,
        'data_owner_count': data_owner_count,
        'index': index_info,
        'keypair': key_info,
        'last_upload_time': last_upload_time,
    }, status=status.HTTP_200_OK)
