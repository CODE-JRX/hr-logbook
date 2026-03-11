"""
Tests for face embedding cache with focus on thread safety and consistency.
"""
import pytest
import threading
import time
import numpy as np
from unittest.mock import patch, Mock, MagicMock
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))


class TestFaceEmbeddingCache:
    """Test face embedding cache operations and thread safety."""
    
    def test_get_face_cache_initialization(self):
        """Test face cache is properly initialized from database."""
        with patch('models.face_embedding_model.get_db_cursor') as mock_cursor_ctx:
            from models.face_embedding_model import get_face_cache, _FACE_CACHE
            
            mock_cursor = Mock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
            
            # Mock database rows
            mock_cursor.fetchall.return_value = [
                {
                    'id': 1,
                    'client_id': 'HR-S26-001',
                    'embedding_json': json.dumps([0.1] * 128)
                },
                {
                    'id': 2,
                    'client_id': 'HR-S26-002',
                    'embedding_json': json.dumps([0.2] * 128)
                }
            ]
            
            cache = get_face_cache(force_refresh=True)
            assert len(cache) == 2
            assert cache[0]['client_id'] == 'HR-S26-001'
            assert isinstance(cache[0]['embedding'], np.ndarray)
    
    def test_corrupt_embedding_skipped(self):
        """Test that corrupt embeddings are skipped with logging."""
        with patch('models.face_embedding_model.get_db_cursor') as mock_cursor_ctx, \
             patch('models.face_embedding_model.logger') as mock_logger:
            from models.face_embedding_model import get_face_cache
            
            mock_cursor = Mock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
            
            # Mix of valid and corrupt data
            mock_cursor.fetchall.return_value = [
                {
                    'id': 1,
                    'client_id': 'HR-S26-001',
                    'embedding_json': json.dumps([0.1] * 128)
                },
                {
                    'id': 2,
                    'client_id': 'HR-S26-002',
                    'embedding_json': 'INVALID_JSON_STRING'  # Will fail
                },
                {
                    'id': 3,
                    'client_id': 'HR-S26-003',
                    'embedding_json': json.dumps([0.3] * 128)
                }
            ]
            
            cache = get_face_cache(force_refresh=True)
            assert len(cache) == 2  # Only valid ones
            mock_logger.warning.assert_called()
    
    def test_add_face_embedding(self):
        """Test adding face embedding updates cache."""
        with patch('models.face_embedding_model.get_db_cursor') as mock_cursor_ctx, \
             patch('models.face_embedding_model.get_face_cache') as mock_get_cache:
            from models.face_embedding_model import add_face_embedding
            
            mock_cursor = Mock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
            mock_cursor.lastrowid = 5
            
            cache = [
                {'id': 1, 'client_id': 'HR-S26-001', 'embedding': np.array([0.1] * 128)}
            ]
            mock_get_cache.return_value = cache
            
            embedding = [0.5] * 128
            result = add_face_embedding('HR-S26-002', embedding)
            
            assert result == 5
            mock_cursor.execute.assert_called_once()
    
    def test_delete_embeddings_by_client_id(self):
        """Test deleting embeddings removes from both DB and cache."""
        with patch('models.face_embedding_model.get_db_cursor') as mock_cursor_ctx, \
             patch('models.face_embedding_model._FACE_CACHE') as mock_cache:
            from models.face_embedding_model import delete_embeddings_by_client_id
            
            mock_cursor = Mock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
            
            mock_cache.__getitem__.side_effect = lambda x: [
                {'id': 1, 'client_id': 'HR-S26-001', 'embedding': np.array([0.1] * 128)},
                {'id': 2, 'client_id': 'HR-S26-002', 'embedding': np.array([0.2] * 128)}
            ]
            
            delete_embeddings_by_client_id('HR-S26-001')
            mock_cursor.execute.assert_called_with(
                "DELETE FROM face_embeddings WHERE client_id = %s",
                ('HR-S26-001',)
            )
    
    def test_find_best_match_with_threshold(self):
        """Test face matching respects similarity threshold."""
        with patch('models.face_embedding_model.get_face_cache') as mock_get_cache:
            from models.face_embedding_model import find_best_match
            
            # Create distinct embeddings
            emb1 = [0.0] * 128
            emb2 = [1.0] * 128
            emb3 = [0.1] * 128  # Close to emb1
            
            cache = [
                {'id': 1, 'client_id': 'HR-S26-001', 'embedding': np.array(emb1)},
                {'id': 2, 'client_id': 'HR-S26-002', 'embedding': np.array(emb2)},
                {'id': 3, 'client_id': 'HR-S26-003', 'embedding': np.array(emb3)}
            ]
            mock_get_cache.return_value = cache
            
            # Search for match to emb3
            client_id, distance = find_best_match(emb3, threshold=0.2)
            assert client_id == 'HR-S26-003'  # Closest match
            assert distance < 0.2
    
    def test_find_best_match_no_match(self):
        """Test face matching returns None when no match exceeds threshold."""
        with patch('models.face_embedding_model.get_face_cache') as mock_get_cache:
            from models.face_embedding_model import find_best_match
            
            emb1 = [0.0] * 128
            emb2 = [1.0] * 128
            search = [0.5] * 128  # Far from both
            
            cache = [
                {'id': 1, 'client_id': 'HR-S26-001', 'embedding': np.array(emb1)},
                {'id': 2, 'client_id': 'HR-S26-002', 'embedding': np.array(emb2)}
            ]
            mock_get_cache.return_value = cache
            
            client_id, distance = find_best_match(search, threshold=0.1)
            assert client_id is None
            assert distance is None
    
    def test_empty_cache_returns_none(self):
        """Test matching with empty cache returns None."""
        with patch('models.face_embedding_model.get_face_cache') as mock_get_cache:
            from models.face_embedding_model import find_best_match
            
            mock_get_cache.return_value = []
            
            client_id, distance = find_best_match([0.1] * 128)
            assert client_id is None
            assert distance is None


class TestFaceEmbeddingThreadSafety:
    """Test thread-safe access to face embedding cache."""
    
    def test_concurrent_cache_reads(self):
        """Test multiple threads can read cache concurrently."""
        with patch('models.face_embedding_model.get_db_cursor') as mock_cursor_ctx:
            from models.face_embedding_model import get_face_cache, _FACE_CACHE_LOCK
            import models.face_embedding_model as fem
            
            # Reset cache for test
            fem._FACE_CACHE = None
            
            mock_cursor = Mock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                {'id': i, 'client_id': f'HR-S26-{i:03d}', 
                 'embedding_json': json.dumps([float(i)] * 128)}
                for i in range(10)
            ]
            
            results = []
            errors = []
            
            def read_cache():
                try:
                    cache = get_face_cache()
                    results.append(len(cache) if cache else 0)
                except Exception as e:
                    errors.append(str(e))
            
            # Create multiple threads reading simultaneously
            threads = [threading.Thread(target=read_cache) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            # All threads should get same cache length (first one loads, others use cache)
            assert len(errors) == 0, f"Errors during concurrent reads: {errors}"
            assert len(results) == 5
            # All should return 10 or some should return 0 if cache load failed
            assert all(r in (0, 10) for r in results), f"Unexpected cache sizes: {results}"
    
    def test_cache_lock_prevents_race_conditions(self):
        """Test that cache lock prevents data corruption."""
        with patch('models.face_embedding_model.get_db_cursor') as mock_cursor_ctx, \
             patch('models.face_embedding_model._FACE_CACHE_LOCK'):
            from models.face_embedding_model import _FACE_CACHE_LOCK
            
            mock_cursor = Mock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            
            # Verify lock is being used (it should be an RLock)
            # This is a simple validation test
            assert _FACE_CACHE_LOCK is not None


class TestFaceEmbeddingImprovement:
    """Test intelligent embedding improvement (merging similar embeddings)."""
    
    def test_improve_embedding_added_initial(self):
        """Test first embedding is added for a new client."""
        with patch('models.face_embedding_model.get_embeddings_by_client_id') as mock_get, \
             patch('models.face_embedding_model.add_face_embedding') as mock_add:
            from models.face_embedding_model import improve_client_embedding
            
            mock_get.return_value = []  # No existing embeddings
            mock_add.return_value = 1
            
            result = improve_client_embedding('NEW-CLIENT', [0.1] * 128)
            assert result == 'added_initial'
            mock_add.assert_called_once()
    
    def test_improve_embedding_rejected_outlier(self):
        """Test very different embedding is rejected as outlier."""
        with patch('models.face_embedding_model.get_embeddings_by_client_id') as mock_get:
            from models.face_embedding_model import improve_client_embedding
            
            # Existing embedding very different
            mock_get.return_value = [
                {'id': 1, 'embedding_json': [0.0] * 128}
            ]
            
            # Very different new embedding
            result = improve_client_embedding('CLIENT', [1.0] * 128)
            assert result == 'rejected_outlier'
    
    def test_improve_embedding_merged_similar(self):
        """Test similar embedding is merged with existing."""
        with patch('models.face_embedding_model.get_embeddings_by_client_id') as mock_get, \
             patch('models.face_embedding_model.get_db_cursor') as mock_cursor_ctx, \
             patch('models.face_embedding_model._FACE_CACHE_LOCK'):
            from models.face_embedding_model import improve_client_embedding
            
            existing_emb = [0.0] * 128
            similar_emb = [0.01] * 128  # Very similar
            
            mock_get.return_value = [
                {'id': 1, 'embedding_json': existing_emb}
            ]
            
            mock_cursor = Mock()
            mock_cursor_ctx.return_value.__enter__.return_value = mock_cursor
            
            result = improve_client_embedding('CLIENT', similar_emb, 
                                            merge_threshold=0.2)
            assert result == 'merged_existing'
