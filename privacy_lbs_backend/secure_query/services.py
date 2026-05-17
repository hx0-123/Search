"""
C1 Cloud Server Service Layer
Implements core logic including secure pruning, task distribution, etc.
"""
import json
import uuid
import time
from typing import List, Dict, Tuple, Optional
from django.core.cache import cache
from django.utils import timezone
from django.db import connection
from .models import SecureQuery, QueryLog
from data_owner.models import EncryptedSpatialObject, DataOwner, IndexMetadata
from indices.ktree import KTree, SpatialObject
from indices.asset_tree import AssetTree
from crypto.paillier_manager import PaillierManager
# Note: Secure protocol requires C1 and C2 cooperation, only importing types here
# from secure_protocols.secure_less_than import SecureLessThanProtocol
# from secure_protocols.secure_squared_euclidean_distance import SecureSquaredEuclideanDistanceProtocol
from fog_node.tasks import compute_encrypted_scores, aggregate_query_results


class C1QueryService:
    """C1 Query Service - The "brain" of the system """

    def __init__(self, public_key: str):
        """
        Initialize C1 service

        Args:
            public_key: Paillier public key (serialized string)
        """
        self.paillier_manager = PaillierManager()
        self.paillier_manager.load_public_key(public_key)
        # Note: C1 only has public key, no private key

    def receive_query(self, query_data: Dict) -> SecureQuery:
        """
        Receive query request

        Args:
            query_data: Query data dictionary

        Returns:
            SecureQuery: Created query object
        """
        query_id = str(uuid.uuid4())

        # Create query object (using retry mechanism for database I/O errors)
        max_retries = 5
        retry_delay = 0.5

        for retry in range(max_retries):
            try:
                # Ensure database connection is active
                connection.ensure_connection()

                # Create directly, without transaction (to avoid nested transaction issues)
                query = SecureQuery.objects.create(
                    query_id=query_id,
                    user=query_data['user'],
                    encrypted_location_x=query_data['encrypted_location_x'],
                    encrypted_location_y=query_data['encrypted_location_y'],
                    encrypted_keywords=json.dumps(query_data['encrypted_keywords']),
                    text_weight=query_data.get('text_weight', 0.5),
                    distance_weight=query_data.get('distance_weight', 0.5),
                    top_k=query_data.get('top_k', 10),
                    is_continuous=query_data.get('is_continuous', False),
                    status='pending'
                )
                break  # Success, exit retry loop
            except Exception as e:
                if retry < max_retries - 1:
                    # Close connection, wait and retry
                    connection.close()
                    time.sleep(retry_delay * (retry + 1))
                    continue
                else:
                    # Last retry failed, raise error
                    raise

        # Prepare log metadata (exclude non-serializable objects)
        log_metadata = {
            'encrypted_location_x': query_data.get('encrypted_location_x', ''),
            'encrypted_location_y': query_data.get('encrypted_location_y', ''),
            'encrypted_keywords': query_data.get('encrypted_keywords', []),
            'text_weight': query_data.get('text_weight', 0.5),
            'distance_weight': query_data.get('distance_weight', 0.5),
            'top_k': query_data.get('top_k', 10),
            'is_continuous': query_data.get('is_continuous', False),
            'user_id': query_data['user'].id if query_data.get('user') else None,
            'username': query_data['user'].username if query_data.get('user') else None
        }

        # Create log (using independent transaction to avoid locking)
        try:
            QueryLog.objects.create(
                query=query,
                log_type='query_received',
                message=f"Query {query_id} received",
                metadata=log_metadata
            )
        except Exception as e:
            # Log creation failure does not affect query, just record error
            print(f"Failed to create query log: {str(e)}")

        return query

    def secure_pruning(self, query: SecureQuery, data_owner: DataOwner) -> List[Dict]:
        """
        Secure Pruning - Two-level pruning process
        Use QL_qi and QS_qi for spatial and keyword pruning

        Args:
            query: Query object
            data_owner: Data owner

        Returns:
            List[Dict]: Candidate object list (encrypted state)
        """
        QueryLog.objects.create(
            query=query,
            log_type='pruning_started',
            message="Starting secure pruning process"
        )

        # Get index metadata
        try:
            index_metadata = IndexMetadata.objects.get(data_owner=data_owner)
        except IndexMetadata.DoesNotExist:
            QueryLog.objects.create(
                query=query,
                log_type='pruning_error',
                message="Index not built for data owner, using fallback: returning all objects"
            )
            # If index does not exist, return all objects as candidates (for testing)
            # In actual production environment, index should be built first
            encrypted_objects = EncryptedSpatialObject.objects.filter(data_owner=data_owner)
            candidates = []
            for obj in encrypted_objects:
                candidates.append({
                    'object_id': obj.object_id,
                    'encrypted_location_x': obj.encrypted_location_x,
                    'encrypted_location_y': obj.encrypted_location_y,
                    'encrypted_keywords': obj.encrypted_keywords,
                    'ktree_node_path': obj.ktree_node_path,
                    'ktree_region': obj.ktree_region
                })
            return candidates

        # First level pruning: Spatial pruning (QL_qi)
        # Use AssetTree for spatial region matching
        spatial_candidates = self._spatial_pruning(query, data_owner, index_metadata)

        QueryLog.objects.create(
            query=query,
            log_type='spatial_pruning_completed',
            message=f"Spatial pruning found {len(spatial_candidates)} candidates",
            metadata={'candidate_count': len(spatial_candidates)}
        )

        # Second level pruning: Keyword pruning (QS_qi)
        keyword_candidates = self._keyword_pruning(query, spatial_candidates, data_owner)

        QueryLog.objects.create(
            query=query,
            log_type='keyword_pruning_completed',
            message=f"Keyword pruning found {len(keyword_candidates)} candidates",
            metadata={'candidate_count': len(keyword_candidates)}
        )

        return keyword_candidates

    def _spatial_pruning(self, query: SecureQuery, data_owner: DataOwner,
                        index_metadata: IndexMetadata) -> List[Dict]:
        """
        Spatial Pruning (QL_qi)
        Use AssetTree and KTree for spatial region matching

        Args:
            query: Query object
            data_owner: Data owner
            index_metadata: Index metadata

        Returns:
            List[Dict]: Spatial candidate objects
        """
        # Load AssetTree from cache or storage (actual implementation needs to load from Redis/Cassandra)
        # Simplified handling here, directly query database

        # Get all encrypted spatial objects
        encrypted_objects = EncryptedSpatialObject.objects.filter(data_owner=data_owner)

        # Simplified: return all objects (should use AssetTree for precise matching in production)
        candidates = []
        for obj in encrypted_objects:
            candidates.append({
                'object_id': obj.object_id,
                'encrypted_location_x': obj.encrypted_location_x,
                'encrypted_location_y': obj.encrypted_location_y,
                'encrypted_keywords': obj.encrypted_keywords,
                'ktree_node_path': obj.ktree_node_path,
                'ktree_region': obj.ktree_region
            })

        return candidates

    def _keyword_pruning(self, query: SecureQuery, spatial_candidates: List[Dict],
                         data_owner: DataOwner) -> List[Dict]:
        """
        Keyword Pruning (QS_qi)
        Use encrypted keyword list for matching

        Args:
            query: Query object
            spatial_candidates: Spatial candidate objects
            data_owner: Data owner

        Returns:
            List[Dict]: Keyword-matched candidate objects
        """
        # Get query keywords
        query_keywords = json.loads(query.encrypted_keywords)

        # Simplified: return all spatial candidates (should use encrypted keyword list for matching in production)
        # In actual implementation, need to use homomorphic encryption for keyword matching
        return spatial_candidates

    def distribute_tasks(self, query: SecureQuery, candidates: List[Dict]) -> List[str]:
        """
        Task Distribution
        Use Celery to package candidate set and query ciphertext into async tasks, distribute to fog nodes

        Args:
            query: Query object
            candidates: Candidate object list

        Returns:
            List[str]: Task ID list
        """
        QueryLog.objects.create(
            query=query,
            log_type='task_distribution_started',
            message=f"Distributing {len(candidates)} candidates to fog nodes"
        )

        # Batch candidate set (each batch processes certain number of objects)
        batch_size = 50
        task_ids = []

        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]

            # Create Celery task
            task = compute_encrypted_scores.delay(
                query_id=query.query_id,
                encrypted_query_x=query.encrypted_location_x,
                encrypted_query_y=query.encrypted_location_y,
                encrypted_query_keywords=query.encrypted_keywords,
                candidates=batch,
                text_weight=query.text_weight,
                distance_weight=query.distance_weight
            )

            task_ids.append(task.id)

            QueryLog.objects.create(
                query=query,
                log_type='task_created',
                message=f"Task {task.id} created for batch {i // batch_size + 1}",
                metadata={'task_id': task.id, 'batch_size': len(batch)}
            )

        # Start aggregation task (automatically aggregate results after all computing tasks complete)
        if task_ids:
            aggregate_query_results.apply_async(
                args=[query.query_id, task_ids],
                countdown=10  # Start checking after 10 seconds (give computing tasks some time)
            )
            QueryLog.objects.create(
                query=query,
                log_type='aggregation_task_created',
                message=f"Aggregation task created for {len(task_ids)} tasks"
            )

        return task_ids

    def aggregate_results(self, query: SecureQuery, task_ids: List[str]) -> List[Dict]:
        """
        Aggregate Results
        Collect computing results from all fog nodes, perform sorting and Top-K selection

        Args:
            query: Query object
            task_ids: Task ID list

        Returns:
            List[Dict]: Top-K result list
        """
        QueryLog.objects.create(
            query=query,
            log_type='result_aggregation_started',
            message=f"Aggregating results from {len(task_ids)} tasks"
        )

        # Wait for all tasks to complete and collect results
        # Note: Cannot call AsyncResult.get() inside Celery tasks, can only get from cache
        all_results = []

        for task_id in task_ids:
            # Get task result from cache (Celery task will store results to cache)
            result_key = f"task_result_{task_id}"
            result = cache.get(result_key)

            if result:
                print(f"[Aggregate] Found result in cache for task {task_id}")
                scores = result.get('scores', [])
                if scores:
                    all_results.extend(scores)
                    QueryLog.objects.create(
                        query=query,
                        log_type='result_retrieved_from_cache',
                        message=f"Retrieved {len(scores)} scores from cache for task {task_id}",
                        metadata={'task_id': task_id, 'score_count': len(scores)}
                    )
            else:
                # If not in cache, check task status
                from celery.result import AsyncResult
                task_result = AsyncResult(task_id)

                print(f"[Aggregate] Task {task_id} state: {task_result.state}, ready: {task_result.ready()}")

                if task_result.ready():
                    # Task completed but no result in cache, possibly cache expiry or configuration issue
                    # Try to get task result directly (only for debugging, avoid in production)
                    try:
                        task_data = task_result.result
                        if isinstance(task_data, dict):
                            scores = task_data.get('scores', [])
                            if scores:
                                all_results.extend(scores)
                                # Also update cache for subsequent use
                                cache.set(result_key, task_data, timeout=3600)
                                QueryLog.objects.create(
                                    query=query,
                                    log_type='result_retrieved_from_task',
                                    message=f"Retrieved {len(scores)} scores directly from task {task_id}",
                                    metadata={'task_id': task_id, 'score_count': len(scores)}
                                )
                            else:
                                QueryLog.objects.create(
                                    query=query,
                                    log_type='task_result_empty',
                                    message=f"Task {task_id} completed but returned no scores",
                                    metadata={'task_id': task_id, 'task_result': str(task_data)[:200]}
                                )
                        else:
                            QueryLog.objects.create(
                                query=query,
                                log_type='task_result_invalid',
                                message=f"Task {task_id} returned invalid result format",
                                metadata={'task_id': task_id, 'result_type': type(task_data).__name__}
                            )
                    except Exception as e:
                        QueryLog.objects.create(
                            query=query,
                            log_type='result_retrieval_error',
                            message=f"Error retrieving result for task {task_id}: {str(e)}",
                            metadata={'task_id': task_id, 'error': str(e)}
                        )
                else:
                    # Task not yet completed, log it
                    QueryLog.objects.create(
                        query=query,
                        log_type='result_not_found_in_cache',
                        message=f"Result not found in cache for task {task_id}, task still running",
                        metadata={'task_id': task_id, 'task_state': task_result.state}
                    )

        # Sort results (development environment: use plaintext score sorting)
        # Production environment: need to use secure protocol for encrypted sorting
        # Sort by composite score descending
        if all_results:
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            print(f"[Aggregate] Sorted {len(all_results)} results, top score: {all_results[0].get('score')}")
        else:
            print(f"[Aggregate] WARNING: No results found from {len(task_ids)} tasks")
            # Print status of each task
            for task_id in task_ids:
                result_key = f"task_result_{task_id}"
                cached = cache.get(result_key)
                task_result = AsyncResult(task_id)
                print(f"  Task {task_id}: cached={cached is not None}, state={task_result.state}, ready={task_result.ready()}")

        # Take Top-K
        top_k_results = all_results[:query.top_k]

        QueryLog.objects.create(
            query=query,
            log_type='result_aggregation_completed',
            message=f"Aggregated {len(top_k_results)} top results from {len(all_results)} total",
            metadata={'result_count': len(top_k_results), 'total_count': len(all_results)}
        )

        return top_k_results


class ContinuousQueryEngine:
    """Continuous Query Engine - Secure area monitoring mechanism"""

    def __init__(self, c1_service: C1QueryService):
        """
        Initialize continuous query engine

        Args:
            c1_service: C1 query service
        """
        self.c1_service = c1_service

    def calculate_secure_area(self, query: SecureQuery) -> Dict:
        """
        Calculate Secure Area (Safe Zone)
        Taking query point as center, dynamically calculate radius:
          radius = max(500m, top_k * 200m), maximum 5000m
        Also store plaintext center coordinates in cache for subsequent check_location_in_secure_area use.
        """
        import base64, json as _json, math

        # Decode from frontend serialization format base64(json({"ciphertext": "<int_scaled>", "exponent": 0})) to real coordinates
        def decode_coord(enc_str: str) -> float:
            try:
                payload = _json.loads(base64.b64decode(enc_str).decode())
                return int(payload['ciphertext']) / 1_000_000
            except Exception:
                return 0.0

        center_lon = decode_coord(query.encrypted_location_x)
        center_lat = decode_coord(query.encrypted_location_y)

        # Dynamic radius: larger top_k means larger radius, minimum 500m, maximum 5000m
        top_k = getattr(query, 'top_k', 10) or 10
        radius = min(5000.0, max(500.0, top_k * 200.0))

        secure_area = {
            'query_id':   query.query_id,
            'encrypted_center_x': query.encrypted_location_x,
            'encrypted_center_y': query.encrypted_location_y,
            'center_lon': center_lon,  # Plaintext, only stored in cache, not returned to frontend
            'center_lat': center_lat,
            'radius':     radius,
            'created_at': timezone.now().isoformat()
        }

        cache_key = f"secure_area_{query.query_id}"
        cache.set(cache_key, secure_area, timeout=3600)

        QueryLog.objects.create(
            query=query,
            log_type='secure_area_calculated',
            message=f"Safe zone: center=({center_lon:.5f},{center_lat:.5f}) radius={radius:.0f}m",
            metadata={'radius': radius, 'center_lon': center_lon, 'center_lat': center_lat}
        )

        return secure_area
    
    def check_location_in_secure_area(self, query: SecureQuery,
                                     new_location_x: str,
                                     new_location_y: str) -> bool:
        """
        Check if new location is within secure area.
        Use Haversine formula with plaintext coordinates (latitude/longitude) to calculate distance,
        compare with secure area radius.
        Only works when coordinates are stored in base64(json) passthrough format;
        returns False (trigger full query) if decoding fails.
        """
        import base64, json as _json, math

        # Get secure area from cache (contains plaintext center coordinates)
        cache_key = f"secure_area_{query.query_id}"
        secure_area = cache.get(cache_key)

        if not secure_area:
            return False

        center_lon = secure_area.get('center_lon')
        center_lat = secure_area.get('center_lat')
        radius     = secure_area.get('radius', 1000.0)

        if center_lon is None or center_lat is None:
            return False

        # Decode new coordinates to plaintext
        def decode_coord(enc_str: str) -> float:
            try:
                payload = _json.loads(base64.b64decode(enc_str).decode())
                return int(payload['ciphertext']) / 1_000_000
            except Exception:
                return None

        new_lon = decode_coord(new_location_x)
        new_lat = decode_coord(new_location_y)

        if new_lon is None or new_lat is None:
            return False

        # Haversine formula: calculate distance between two points (meters)
        R = 6_371_000  # Earth radius (meters)
        phi1 = math.radians(center_lat)
        phi2 = math.radians(new_lat)
        d_phi = math.radians(new_lat - center_lat)
        d_lam = math.radians(new_lon - center_lon)
        a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
        distance_m = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        in_zone = distance_m <= radius

        # Log lightweight entry (non-blocking)
        try:
            QueryLog.objects.create(
                query=query,
                log_type='safe_zone_check',
                message=f"distance={distance_m:.1f}m radius={radius:.1f}m in_zone={in_zone}",
                metadata={'distance_m': round(distance_m, 1), 'radius': radius, 'in_zone': in_zone}
            )
        except Exception:
            pass

        return in_zone

    def handle_location_update(self, query: SecureQuery,
                               new_location_x: str,
                               new_location_y: str) -> Dict:
        """
        Handle location update

        Args:
            query: Query object
            new_location_x: New encrypted X coordinate
            new_location_y: New encrypted Y coordinate

        Returns:
            Dict: Processing result
        """
        QueryLog.objects.create(
            query=query,
            log_type='location_update_received',
            message="Location update received for continuous query"
        )

        # Check if within secure area
        in_secure_area = self.check_location_in_secure_area(
            query, new_location_x, new_location_y
        )

        if in_secure_area:
            # Within secure area, try memory cache first, then database for latest results
            cache_key = f"query_result_{query.query_id}"
            cached_result = cache.get(cache_key)

            if not cached_result and query.encrypted_results:
                # Cache expired but database has results, use database results directly
                try:
                    cached_result = json.loads(query.encrypted_results)
                except Exception:
                    cached_result = None

            if cached_result:
                QueryLog.objects.create(
                    query=query,
                    log_type='cached_result_returned',
                    message="Returned cached result (within safe zone)"
                )
                return {
                    'status': 'cached',
                    'result': cached_result
                }

        # Outside secure area (or no cache available), trigger full query
        QueryLog.objects.create(
            query=query,
            log_type='full_query_triggered',
            message="Triggering full query (outside secure area)"
        )
        
        # Update query location
        query.encrypted_location_x = new_location_x
        query.encrypted_location_y = new_location_y
        query.save()
        
        # Recalculate secure area
        secure_area = self.calculate_secure_area(query)
        
        return {
            'status': 'full_query',
            'secure_area': secure_area,
            'message': 'Full query triggered, secure area updated'
        }

