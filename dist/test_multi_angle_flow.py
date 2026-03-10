import unittest
from unittest.mock import MagicMock, patch
import json
import numpy as np
from models.face_embedding_model import add_face_embedding, find_best_match
from models.client_model import add_client, delete_client, get_client_by_client_id

class TestMultiAngleFacerecognition(unittest.TestCase):
    
    def setUp(self):
        self.client_id = "TEST-MULTI-001"
        self.full_name = "Test Multi Angle"
        # Create a dummy client
        add_client(self.client_id, "TEST", "MULTI ANGLE", mi="", name_ext="", department="TEST_DEPT", gender="MALE", age=30, client_type="VISITOR")
        
        # Create 3 dummy embeddings (random vectors of length 128)
        # We'll make them distinct but recognizable
        self.center_emb = np.random.rand(128).tolist()
        self.left_emb = np.random.rand(128).tolist()
        self.right_emb = np.random.rand(128).tolist()
        
    def tearDown(self):
        # Clean up
        delete_client(self.client_id) # Should cascade delete embeddings if schema is correct, otherwise we might leave orphans but that's okay for test DB

    def test_multi_angle_matching(self):
        # 1. Add 3 embeddings
        print("Adding Center embedding...")
        add_face_embedding(self.client_id, self.center_emb)
        print("Adding Left embedding...")
        add_face_embedding(self.client_id, self.left_emb)
        print("Adding Right embedding...")
        add_face_embedding(self.client_id, self.right_emb)
        
        # 2. Verify recognition for exact matches (sanity check)
        print("Testing exact match for Left embedding...")
        matched_id, dist = find_best_match(self.left_emb)
        self.assertEqual(matched_id, self.client_id)
        self.assertLess(dist, 0.001)
        
        print("Testing exact match for Right embedding...")
        matched_id, dist = find_best_match(self.right_emb)
        self.assertEqual(matched_id, self.client_id)
        self.assertLess(dist, 0.001)
        
        # 3. Verify recognition for close match (simulating noise)
        print("Testing close match for Center embedding...")
        noisy_center = [x + 0.01 for x in self.center_emb]
        matched_id, dist = find_best_match(noisy_center)
        self.assertEqual(matched_id, self.client_id)
        # Distance should be small
        
        print("\nMulti-angle recognition verification successful!")

if __name__ == '__main__':
    unittest.main()
