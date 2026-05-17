from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
import json
from typing import List, Dict
from secure_query.models import QueryLog, SecureQuery
from data_owner.models import DataOwner
from secure_protocols.secure_squared_euclidean_distance import SecureSquaredEuclideanDistanceProtocol
from crypto.paillier_manager import PaillierManager


@shared_task(bind=True, name='fog_node.compute_encrypted_scores')
def compute_encrypted_scores(self, query_id: str, encrypted_query_x: str,
                            encrypted_query_y: str, encrypted_query_keywords: str,
                            candidates: List[Dict], text_weight: float,
                            distance_weight: float) -> Dict:
    
    try:
        # Record task start
        import time
        start_time = time.time()
        task_log = f"Task {self.request.id} started for query {query_id}, candidates: {len(candidates)}"
        print(task_log)
        
        # Get query location (plaintext, for development environment calculation)
        # Note: In production, these calculations should be performed in encrypted domain
        from data_owner.models import EncryptedSpatialObject, DataOwner
        import math
        
        # Get data owner to access original locations (use most recently uploaded DataOwner)
        try:
            data_owner = DataOwner.objects.filter(index_built=True).order_by('-updated_at').first()
            if not data_owner:
                data_owner = DataOwner.objects.order_by('-updated_at').first()
            if not data_owner:
                raise ValueError("Data owner not found")
        except Exception as e:
            error_msg = f"Failed to get data owner: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
        
        # Parse query location
        # Frontend uses serializeAsPassthrough to encode coordinates as base64(json({ciphertext, exponent}))
        # Format: base64( json({"ciphertext": "<int_scaled_1e6>", "exponent": 0}) )
        import base64 as _base64
        PRECISION = 1_000_000

        def _decode_coord(enc_str: str) -> float:
            """Decode base64-encoded coordinates from frontend, return original float value"""
            try:
                # Try base64 decoding
                decoded = _base64.b64decode(enc_str + '==').decode('utf-8')
                obj = json.loads(decoded)
                return int(obj['ciphertext']) / PRECISION
            except Exception:
                pass
            try:
                # Directly try float (compatible with old format)
                return float(enc_str)
            except (ValueError, TypeError):
                return None

        query_x = _decode_coord(encrypted_query_x)
        query_y = _decode_coord(encrypted_query_y)

        if query_x is None or query_y is None:
            print(f"[Task] WARNING: Failed to decode query coordinates, using defaults")
            query_x = query_x or 116.4074
            query_y = query_y or 39.9042
        else:
            print(f"[Task] Decoded query coords: x={query_x}, y={query_y}")

        # Parse query keywords (frontend sends plaintext string array)
        query_keywords = json.loads(encrypted_query_keywords) if isinstance(encrypted_query_keywords, str) else encrypted_query_keywords
        # Filter actual string keywords (exclude encrypted values like integers)
        query_keywords_str = [kw for kw in query_keywords if isinstance(kw, str)]
        query_keywords_lower = [kw.lower() for kw in query_keywords_str]
        
        # Batch fetch data for all candidate objects (optimization: avoid N+1 queries)
        object_ids = [c.get('object_id') for c in candidates if c.get('object_id')]
        
        # Query all objects' locations and keywords in one batch
        objects_dict = {}
        if object_ids:
            try:
                objects = EncryptedSpatialObject.objects.filter(
                    data_owner=data_owner,
                    object_id__in=object_ids
                ).values('object_id', 'original_x', 'original_y', 'encrypted_keywords', 'metadata')
                
                for obj in objects:
                    objects_dict[obj['object_id']] = obj
                
                print(f"Loaded {len(objects_dict)} objects from database for {len(object_ids)} candidates")
            except Exception as e:
                print(f"Warning: Failed to load objects from database: {str(e)}")
                # Continue execution with default values
        
        encrypted_scores = []
        
        for candidate in candidates:
            object_id = candidate.get('object_id')
            
            # Get object data from batch query results
            obj_name = object_id  # Default to object_id as name
            if object_id in objects_dict:
                obj = objects_dict[object_id]
                obj_x = obj.get('original_x') or 116.4074
                obj_y = obj.get('original_y') or 39.9042
                
                # Get readable name and original plaintext keywords from metadata
                obj_metadata = obj.get('metadata') or {}
                if isinstance(obj_metadata, str):
                    try:
                        obj_metadata = json.loads(obj_metadata)
                    except:
                        obj_metadata = {}
                obj_name = obj_metadata.get('name') or obj_metadata.get('document') or object_id

                # Prefer original plaintext keywords stored in metadata (direct match with query keywords)
                # encrypted_keywords stores encrypted integers, cannot be used for text matching
                meta_keywords = obj_metadata.get('keywords', [])
                if meta_keywords and isinstance(meta_keywords, list):
                    obj_keywords_lower = [kw.lower() for kw in meta_keywords if isinstance(kw, str)]
                else:
                    # fallback: try to get string keywords from encrypted_keywords
                    obj_keywords_json = obj.get('encrypted_keywords', '[]')
                    try:
                        obj_keywords = json.loads(obj_keywords_json) if isinstance(obj_keywords_json, str) else obj_keywords_json
                        obj_keywords_lower = [kw.lower() for kw in obj_keywords if isinstance(kw, str)]
                    except:
                        obj_keywords_lower = []
            else:
                # If object not found, use default values
                obj_x = 116.4074
                obj_y = 39.9042
                obj_keywords_lower = []
            
            # Calculate distance (Haversine formula)
            R = 6371000  # Earth radius (meters)
            lat1_rad = math.radians(query_y)
            lat2_rad = math.radians(obj_y)
            dlat = math.radians(obj_y - query_y)
            dlon = math.radians(obj_x - query_x)
            
            a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance_meters = R * c
            
            # Calculate distance score (smaller distance = higher score)
            # Using inverse function: score = 1 / (1 + distance / max_distance)
            # max_distance set to 10km, score range approx 0.09-1.0
            max_distance = 10000  # 10km
            distance_score = 1.0 / (1.0 + distance_meters / max_distance)
            
            # Calculate text matching score (based on keyword matching)
            if query_keywords_lower and obj_keywords_lower:
                # Calculate Jaccard similarity
                query_set = set(query_keywords_lower)
                obj_set = set(obj_keywords_lower)
                intersection = query_set & obj_set
                union = query_set | obj_set
                text_score = len(intersection) / len(union) if union else 0.0
            else:
                text_score = 0.0
            
            # Calculate combined score
            combined_score = text_weight * text_score + distance_weight * distance_score
            
            # Encrypt scores using Paillier homomorphic encryption
            try:
                # Get data owner's public key
                paillier_manager = PaillierManager()
                paillier_manager.load_public_key(data_owner.public_key)
                
                # Encrypt individual scores (convert to integer first)
                encrypted_distance_score = paillier_manager.encrypt(distance_score)
                encrypted_text_score = paillier_manager.encrypt(text_score)
                encrypted_combined_score = paillier_manager.encrypt(combined_score)
            except Exception as e:
                print(f"Warning: Failed to encrypt scores: {str(e)}, using plaintext fallback")
                encrypted_distance_score = 'encryption_failed'
                encrypted_text_score = 'encryption_failed'
                encrypted_combined_score = 'encryption_failed'
            
            # Build result (contains encrypted scores)
            encrypted_score = {
                'object_id': object_id,
                'name': obj_name,  # Readable name (for frontend display)
                'score': round(combined_score, 4),  # Combined score (plaintext, for frontend sorting)
                'distance_score': round(distance_score, 4),  # Distance score (plaintext, for display)
                'text_score': round(text_score, 4),  # Text score (plaintext, for display)
                'distance_meters': round(distance_meters, 2),  # Distance (meters, plaintext, for display)
                'encrypted_distance_score': encrypted_distance_score,  # Encrypted distance score
                'encrypted_text_score': encrypted_text_score,     # Encrypted text score
                'encrypted_combined_score': encrypted_combined_score  # Encrypted combined score
            }
            
            encrypted_scores.append(encrypted_score)
        
        # Store results in cache (for C1 aggregation)
        result_key = f"task_result_{self.request.id}"
        result_data = {
            'query_id': query_id,
            'task_id': self.request.id,
            'scores': encrypted_scores,
            'candidate_count': len(candidates)
        }
        
        try:
            cache.set(result_key, result_data, timeout=3600)
            print(f"Task {self.request.id} results cached successfully")
        except Exception as e:
            print(f"Warning: Failed to cache results: {str(e)}")
            # Continue execution, results will still be returned
        
        elapsed_time = time.time() - start_time
        task_log = f"Task {self.request.id} completed, computed {len(encrypted_scores)} encrypted scores in {elapsed_time:.2f}s"
        print(task_log)
        
        # Print first 3 result scores (for debugging)
        if encrypted_scores:
            print(f"Sample encrypted scores:")
            for i, score in enumerate(encrypted_scores[:3]):
                enc_combined = score.get('encrypted_combined_score', '')
                enc_preview = enc_combined[:50] + '...' if isinstance(enc_combined, str) and len(enc_combined) > 50 else enc_combined
                print(f"  {i+1}. {score.get('object_id')}: plaintext_score={score.get('score')}, encrypted_combined_score={enc_preview}")
        
        return result_data
        
    except Exception as e:
        # Log error
        error_log = f"Task {self.request.id} failed: {str(e)}"
        print(error_log)
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task(bind=True, name='fog_node.aggregate_query_results')
def aggregate_query_results(self, query_id: str, task_ids: List[str]):
    """
    Aggregate query results
    After all computation tasks complete, aggregate results and update query status
    
    Args:
        query_id: Query ID
        task_ids: List of task IDs
    """
    try:
        # Get query object
        query = SecureQuery.objects.get(query_id=query_id)
        
        # Check if all tasks are completed
        # Determine task completion by checking if results exist in cache
        # Note: Cannot call AsyncResult.get() inside Celery tasks, only check cache
        from celery.result import AsyncResult
        
        all_ready = True
        for task_id in task_ids:
            # First check cache
            result_key = f"task_result_{task_id}"
            if cache.get(result_key):
                continue  # Result exists in cache, task completed
            
            # If not in cache, check task status (but don't call get())
            task_result = AsyncResult(task_id)
            if not task_result.ready():
                all_ready = False
                break
        
        if not all_ready:
            # If some tasks are not completed yet, retry later
            QueryLog.objects.create(
                query=query,
                log_type='aggregation_deferred',
                message=f"Not all tasks completed yet, will retry"
            )
            raise self.retry(countdown=5, max_retries=60)  # Retry up to 60 times, 5 seconds each
        
        # All tasks completed, start aggregating results
        try:
            data_owner = DataOwner.objects.filter(index_built=True).order_by('-updated_at').first()
            if not data_owner:
                data_owner = DataOwner.objects.order_by('-updated_at').first()
            if not data_owner:
                QueryLog.objects.create(
                    query=query,
                    log_type='aggregation_error',
                    message="Data owner not found"
                )
                query.status = 'failed'
                query.save()
                return
            
            # Avoid circular import, import inside function
            from secure_query.services import C1QueryService
            c1_service = C1QueryService(data_owner.public_key)
            results = c1_service.aggregate_results(query, task_ids)
            
            # Add location info to results (critical fix: add location during aggregation)
            if results:
                from data_owner.models import EncryptedSpatialObject
                
                # Get object IDs for all results
                object_ids = [result.get('object_id') for result in results if result.get('object_id')]
                
                # Batch query object location info (also get metadata for readable names)
                objects = EncryptedSpatialObject.objects.filter(
                    data_owner=data_owner,
                    object_id__in=object_ids
                ).values('object_id', 'original_x', 'original_y', 'metadata', 'encrypted_name')
                
                # Create location mapping
                location_map = {obj['object_id']: obj for obj in objects}
                
                # Add location info to each result
                for result in results:
                    object_id = result.get('object_id')
                    if object_id in location_map:
                        obj_info = location_map[object_id]
                        # Add location info (use original location for frontend display)
                        result['location'] = {
                            'longitude': obj_info.get('original_x') or 116.4074,
                            'latitude': obj_info.get('original_y') or 39.9042,
                        }
                        # Extract readable name from metadata (if scoring task didn't provide)
                        if 'name' not in result:
                            obj_metadata = obj_info.get('metadata') or {}
                            if isinstance(obj_metadata, str):
                                try:
                                    import json as _json
                                    obj_metadata = _json.loads(obj_metadata)
                                except:
                                    obj_metadata = {}
                            readable_name = obj_metadata.get('name') or obj_metadata.get('document')
                            if readable_name:
                                result['name'] = readable_name
                        # Return encrypted_name for frontend decryption demo
                        if obj_info.get('encrypted_name') and 'encrypted_name' not in result:
                            result['encrypted_name'] = obj_info['encrypted_name']
                    else:
                        # If object not found, use default location
                        result['location'] = {
                            'longitude': 116.4074,
                            'latitude': 39.9042,
                        }
            
            # Update query status
            if results:
                query.encrypted_results = json.dumps(results, ensure_ascii=False)
                query.status = 'completed'
                query.completed_at = timezone.now()
                query.save()
                
                QueryLog.objects.create(
                    query=query,
                    log_type='result_aggregated',
                    message=f"Results aggregated successfully with locations, {len(results)} results",
                    metadata={'result_count': len(results)}
                )
            else:
                query.status = 'completed'
                query.completed_at = timezone.now()
                query.save()
                
                QueryLog.objects.create(
                    query=query,
                    log_type='result_empty',
                    message="All tasks completed but no results found"
                )
                
        except Exception as e:
            QueryLog.objects.create(
                query=query,
                log_type='aggregation_error',
                message=f"Error aggregating results: {str(e)}",
                metadata={'error': str(e)}
            )
            query.status = 'failed'
            query.save()
            
    except SecureQuery.DoesNotExist:
        print(f"Query {query_id} not found")
    except Exception as e:
        error_log = f"Aggregation task failed: {str(e)}"
        print(error_log)
        raise self.retry(exc=e, countdown=10, max_retries=3)

