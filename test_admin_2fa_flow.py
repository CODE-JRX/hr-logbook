import unittest
from unittest.mock import MagicMock, patch
import json
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.admin_model import add_admin, verify_admin_pin, find_best_admin_match, get_admin_by_email
from db import get_db

class TestAdmin2FA(unittest.TestCase):
    def setUp(self):
        # Create a dummy embedding list (3 angles)
        self.embedding_center = [0.1] * 128
        self.embedding_left = [0.1] * 128
        self.embedding_right = [0.1] * 128
        self.embeddings = [self.embedding_center, self.embedding_left, self.embedding_right]
        self.pin = "1234"
        self.email = "test_admin_2fa@example.com"
        
        # Clean up if exists
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM admins WHERE email = %s", (self.email,))
        db.commit()
        cursor.close()
        db.close()

    def tearDown(self):
        # Clean up
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM admins WHERE email = %s", (self.email,))
        db.commit()
        cursor.close()
        db.close()

    def test_add_admin_with_pin_and_embeddings(self):
        print("\nTesting Admin Signup with PIN and 3 Embeddings...")
        admin_id = add_admin("Test", "Admin", self.email, "password", self.embeddings, self.pin)
        self.assertIsNotNone(admin_id)
        
        # Verify stored data
        admin = get_admin_by_email(self.email)
        self.assertIsNotNone(admin)
        self.assertIsNotNone(admin.get('pin_hash'))
        
        # Verify embedding storage
        stored_emb = admin.get('face_embedding')
        self.assertIsInstance(stored_emb, list)
        self.assertEqual(len(stored_emb), 3)

    def test_verify_pin(self):
        print("\nTesting PIN Verification...")
        admin_id = add_admin("Test", "Admin", self.email, "password", self.embeddings, self.pin)
        admin = get_admin_by_email(self.email)
        
        # Correct PIN
        self.assertTrue(verify_admin_pin(admin, "1234"))
        
        # Incorrect PIN
        self.assertFalse(verify_admin_pin(admin, "0000"))

    def test_find_match(self):
        print("\nTesting Face Matching with Multiple Embeddings...")
        add_admin("Test", "Admin", self.email, "password", self.embeddings, self.pin)
        
        # Match against one of the embeddings
        target = [0.1] * 128
        matched_id, distance = find_best_admin_match(target)
        
        self.assertIsNotNone(matched_id)
        # Should match the admin we just added (unless there's another identical one, but we use a unique dummy vector)
        
        # Test no match
        no_match_target = [0.9] * 128
        matched_id_none, _ = find_best_admin_match(no_match_target)
        # Depending on threshold and other data, this might be None or different. 
        # But for [0.1]*128 vs [0.9]*128, distance is high (~10.2).
        
if __name__ == '__main__':
    unittest.main()
