"""
Unit tests for SharedContextManager
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime

from memory.shared_context_manager import SharedContextManager, ContextVersion, AccessControl

class TestSharedContextManager(unittest.TestCase):
    """Test cases for SharedContextManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.memory_manager = MagicMock()
        self.shared_context_manager = SharedContextManager(self.memory_manager)
        
        # Mock event_bus
        patcher = patch('memory.shared_context_manager.event_bus')
        self.mock_event_bus = patcher.start()
        self.addCleanup(patcher.stop)
        
        # Mock event_cache_manager
        patcher2 = patch('memory.shared_context_manager.EventCacheManager')
        mock_event_cache_manager_class = patcher2.start()
        self.mock_event_cache_manager = MagicMock()
        mock_event_cache_manager_class.return_value = self.mock_event_cache_manager
        self.addCleanup(patcher2.stop)
    
    def test_init(self):
        """Test initialization"""
        self.assertEqual(self.shared_context_manager.memory_manager, self.memory_manager)
        self.assertEqual(self.shared_context_manager.context_versions, {})
        self.assertEqual(self.shared_context_manager.access_controls, {})
        self.assertTrue(hasattr(self.shared_context_manager, 'role_hierarchy'))
        self.mock_event_bus.subscribe.assert_called_once_with(
            "shared_context_updated", 
            self.shared_context_manager._handle_context_update
        )
    
    def test_check_read_access(self):
        """Test read access control"""
        # Create a test context with access control
        context_id = "test_context"
        self.shared_context_manager.access_controls[context_id] = AccessControl(
            read_roles={"manager", "finance"},
            write_roles={"manager"},
            owner="cofounder"
        )
        
        # Owner should have read access
        self.assertTrue(self.shared_context_manager._check_read_access(context_id, "cofounder"))
        
        # Roles with explicit read access should have read access
        self.assertTrue(self.shared_context_manager._check_read_access(context_id, "manager"))
        self.assertTrue(self.shared_context_manager._check_read_access(context_id, "finance"))
        
        # Roles with higher hierarchy than granted roles should have read access
        self.assertTrue(self.shared_context_manager._check_read_access(context_id, "strategy"))
        
        # Roles with lower hierarchy than granted roles should not have read access
        self.assertFalse(self.shared_context_manager._check_read_access(context_id, "marketing"))
        
        # Non-existent context should return False
        self.assertFalse(self.shared_context_manager._check_read_access("non_existent", "cofounder"))
    
    def test_check_write_access(self):
        """Test write access control"""
        # Create a test context with access control
        context_id = "test_context"
        self.shared_context_manager.access_controls[context_id] = AccessControl(
            read_roles={"manager", "finance", "marketing"},
            write_roles={"manager"},
            owner="cofounder"
        )
        
        # Owner should have write access
        self.assertTrue(self.shared_context_manager._check_write_access(context_id, "cofounder"))
        
        # Roles with explicit write access should have write access
        self.assertTrue(self.shared_context_manager._check_write_access(context_id, "manager"))
        
        # Roles with only read access should not have write access
        self.assertFalse(self.shared_context_manager._check_write_access(context_id, "finance"))
        self.assertFalse(self.shared_context_manager._check_write_access(context_id, "marketing"))
        
        # Roles with higher hierarchy than granted roles should NOT have write access
        # (write access doesn't use hierarchy)
        self.assertFalse(self.shared_context_manager._check_write_access(context_id, "strategy"))
        
        # Non-existent context should return False
        self.assertFalse(self.shared_context_manager._check_write_access("non_existent", "cofounder"))
    
    def test_get_latest_version(self):
        """Test getting the latest version of a context"""
        # Create a test context with multiple versions
        context_id = "test_context"
        version1 = ContextVersion(
            version_id="v1",
            content={"data": "version 1"},
            created_by="agent1",
            created_at="2025-01-01T00:00:00"
        )
        version2 = ContextVersion(
            version_id="v2",
            content={"data": "version 2"},
            created_by="agent1",
            created_at="2025-01-02T00:00:00"
        )
        
        # Add versions to context
        self.shared_context_manager.context_versions[context_id] = [version1, version2]
        
        # Get latest version
        latest = self.shared_context_manager._get_latest_version(context_id)
        
        # Should return version2 (latest by timestamp)
        self.assertEqual(latest.version_id, "v2")
        self.assertEqual(latest.content, {"data": "version 2"})
        
        # Non-existent context should return None
        self.assertIsNone(self.shared_context_manager._get_latest_version("non_existent"))
        
        # Empty versions list should return None
        self.shared_context_manager.context_versions["empty"] = []
        self.assertIsNone(self.shared_context_manager._get_latest_version("empty"))

    async def async_test_store_shared_context(self):
        """Test storing shared context"""
        # Set up memory manager mock
        self.memory_manager.store_agent_memory.return_value = "timestamp"
        
        # Store shared context
        context_id = await self.shared_context_manager.store_shared_context(
            context_type="test",
            content={"data": "test data"},
            source_agent="agent1",
            confidence=0.9
        )
        
        # Check that memory manager was called
        self.memory_manager.store_agent_memory.assert_called_once()
        call_args = self.memory_manager.store_agent_memory.call_args[1]
        self.assertEqual(call_args["agent_name"], "agent1")
        self.assertEqual(call_args["memory_type"], "shared_context_test")
        self.assertEqual(call_args["content"], {"data": "test data"})
        self.assertTrue(call_args["is_shared"])
        self.assertEqual(call_args["confidence"], 0.9)
        
        # Check that event was published
        self.mock_event_bus.publish.assert_called_once()
        event_args = self.mock_event_bus.publish.call_args[0]
        self.assertEqual(event_args[0], "shared_context_updated")
        self.assertEqual(event_args[1]["context_type"], "test")
        self.assertEqual(event_args[1]["source_agent"], "agent1")
        
        # Check that context was stored in memory
        self.assertTrue(context_id in self.shared_context_manager.context_versions)
        self.assertEqual(len(self.shared_context_manager.context_versions[context_id]), 1)
        self.assertEqual(
            self.shared_context_manager.context_versions[context_id][0].content,
            {"data": "test data"}
        )
        
        # Check that access control was set up
        self.assertTrue(context_id in self.shared_context_manager.access_controls)
        self.assertEqual(self.shared_context_manager.access_controls[context_id].owner, "agent1")
        
        return context_id

    async def async_test_update_shared_context(self):
        """Test updating shared context"""
        # First store a context
        context_id = await self.async_test_store_shared_context()
        
        # Reset mocks
        self.memory_manager.store_agent_memory.reset_mock()
        self.mock_event_bus.publish.reset_mock()
        
        # Update the context
        result = await self.shared_context_manager.update_shared_context(
            context_id=context_id,
            updates={"new_field": "new value"},
            updating_agent="agent1",
            change_description="Added new field"
        )
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["context_id"], context_id)
        self.assertEqual(result["updated_by"], "agent1")
        
        # Check that memory manager was called
        self.memory_manager.store_agent_memory.assert_called_once()
        
        # Check that a new version was created
        self.assertEqual(len(self.shared_context_manager.context_versions[context_id]), 2)
        latest = self.shared_context_manager._get_latest_version(context_id)
        self.assertEqual(latest.content, {"data": "test data", "new_field": "new value"})
        self.assertEqual(latest.change_description, "Added new field")
        
        # Test update with no write access
        result = await self.shared_context_manager.update_shared_context(
            context_id=context_id,
            updates={"field": "value"},
            updating_agent="marketing",  # No write access
            change_description="This should fail"
        )
        
        # Should return error
        self.assertTrue("error" in result)
        self.assertEqual(result["error"], "access_denied")

    async def async_test_get_shared_context(self):
        """Test getting shared context"""
        # First store some contexts
        await self.async_test_store_shared_context()  # This creates "test" type context
        
        # Store another context with different type
        await self.shared_context_manager.store_shared_context(
            context_type="report",
            content={"report_data": "important findings"},
            source_agent="finance",
            confidence=0.95
        )
        
        # Set up memory manager mock for query
        self.memory_manager.query_agent_memory.return_value = [
            {
                "content": {"data": "test data"},
                "author": "agent1",
                "timestamp": "2025-01-01T00:00:00",
                "metadata": {
                    "context_id": "test_20250101000000",
                    "version_id": "test_20250101000000_v20250101000000"
                }
            },
            {
                "content": {"report_data": "important findings"},
                "author": "finance",
                "timestamp": "2025-01-02T00:00:00",
                "metadata": {
                    "context_id": "report_20250102000000",
                    "version_id": "report_20250102000000_v20250102000000"
                }
            }
        ]
        
        # Get all shared contexts
        contexts = await self.shared_context_manager.get_shared_context(
            requesting_agent="manager"  # Manager has access to all
        )
        
        # Should return both contexts
        self.assertEqual(len(contexts), 2)
        
        # Get contexts by type
        self.memory_manager.query_agent_memory.reset_mock()
        self.memory_manager.query_agent_memory.return_value = [
            {
                "content": {"report_data": "important findings"},
                "author": "finance",
                "timestamp": "2025-01-02T00:00:00",
                "metadata": {
                    "context_id": "report_20250102000000",
                    "version_id": "report_20250102000000_v20250102000000"
                }
            }
        ]
        
        contexts = await self.shared_context_manager.get_shared_context(
            context_type="report",
            requesting_agent="manager"
        )
        
        # Should return only report context
        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0]["content"], {"report_data": "important findings"})
        
        # Test semantic search
        self.memory_manager.query_agent_memory.reset_mock()
        self.memory_manager.semantic_search.return_value = [
            {
                "content": {"data": "test data"},
                "metadata": {
                    "context_id": "test_20250101000000",
                    "version_id": "test_20250101000000_v20250101000000",
                    "agent": "agent1"
                },
                "timestamp": "2025-01-01T00:00:00",
                "score": 0.95
            }
        ]
        
        contexts = await self.shared_context_manager.get_shared_context(
            query="test data",
            requesting_agent="manager"
        )
        
        # Should return matching context
        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0]["content"], {"data": "test data"})
        self.assertEqual(contexts[0]["relevance_score"], 0.95)

    async def async_test_grant_revoke_access(self):
        """Test granting and revoking access"""
        # First store a context
        context_id = await self.async_test_store_shared_context()
        
        # Grant read access to marketing
        result = await self.shared_context_manager.grant_access(
            context_id=context_id,
            granting_agent="agent1",  # Owner
            target_role="marketing",
            access_type="read"
        )
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["context_id"], context_id)
        self.assertEqual(result["target_role"], "marketing")
        self.assertEqual(result["access_type"], "read")
        
        # Check that access was granted
        self.assertTrue("marketing" in self.shared_context_manager.access_controls[context_id].read_roles)
        
        # Grant write access to finance
        result = await self.shared_context_manager.grant_access(
            context_id=context_id,
            granting_agent="agent1",  # Owner
            target_role="finance",
            access_type="write"
        )
        
        # Check that access was granted
        self.assertTrue("finance" in self.shared_context_manager.access_controls[context_id].write_roles)
        
        # Try to grant access as non-owner
        result = await self.shared_context_manager.grant_access(
            context_id=context_id,
            granting_agent="marketing",  # Not owner
            target_role="strategy",
            access_type="read"
        )
        
        # Should return error
        self.assertTrue("error" in result)
        self.assertEqual(result["error"], "access_denied")
        
        # Revoke read access from marketing
        result = await self.shared_context_manager.revoke_access(
            context_id=context_id,
            revoking_agent="agent1",  # Owner
            target_role="marketing",
            access_type="read"
        )
        
        # Check result
        self.assertTrue(result["success"])
        
        # Check that access was revoked
        self.assertFalse("marketing" in self.shared_context_manager.access_controls[context_id].read_roles)

    def test_async_methods(self):
        """Run async tests"""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test_store_shared_context())
        loop.run_until_complete(self.async_test_update_shared_context())
        loop.run_until_complete(self.async_test_get_shared_context())
        loop.run_until_complete(self.async_test_grant_revoke_access())

if __name__ == "__main__":
    unittest.main()