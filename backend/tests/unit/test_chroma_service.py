"""Tests for ChromaDB service."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from backend.services.chroma_service import ChromaService


@pytest.mark.unit
class TestChromaService:
    """Tests for ChromaDB service."""

    @patch("backend.services.chroma_service.chromadb.PersistentClient")
    @patch("backend.services.chroma_service.get_settings")
    def test_init(self, mock_get_settings, mock_client):
        """Test ChromaService initialization."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.vectordb.persist_directory = "./test_data/chroma"
        mock_get_settings.return_value = mock_settings

        # Create service
        service = ChromaService()

        # Verify client was created
        mock_client.assert_called_once()
        assert service.client is not None

    @patch("backend.services.chroma_service.chromadb.PersistentClient")
    @patch("backend.services.chroma_service.get_settings")
    def test_store_memory(self, mock_get_settings, mock_client):
        """Test storing a memory."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.vectordb.persist_directory = "./test_data/chroma"
        mock_get_settings.return_value = mock_settings

        # Mock collection
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_collection.side_effect = Exception("Not found")
        mock_client_instance.create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        # Create service
        service = ChromaService()

        # Store memory
        doc_id = service.store_memory(
            user_id="test_user",
            content="Test memory content",
            metadata={"category": "preference"},
        )

        # Verify collection was created and add was called
        assert doc_id.startswith("mem_test_user_")
        mock_collection.add.assert_called_once()

    @patch("backend.services.chroma_service.chromadb.PersistentClient")
    @patch("backend.services.chroma_service.get_settings")
    def test_lookup_memories(self, mock_get_settings, mock_client):
        """Test looking up memories."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.vectordb.persist_directory = "./test_data/chroma"
        mock_get_settings.return_value = mock_settings

        # Mock collection with query results
        mock_collection = Mock()
        mock_collection.count.return_value = 1
        mock_collection.query.return_value = {
            "ids": [["mem_1"]],
            "documents": [["Test memory"]],
            "metadatas": [[{"user_id": "test_user"}]],
            "distances": [[0.1]],
        }

        mock_client_instance = Mock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        # Create service
        service = ChromaService()

        # Lookup memories
        results = service.lookup_memories(
            user_id="test_user", query="test query", limit=5
        )

        # Verify results
        assert len(results) == 1
        assert results[0]["id"] == "mem_1"
        assert results[0]["content"] == "Test memory"
        assert results[0]["distance"] == 0.1

    @patch("backend.services.chroma_service.chromadb.PersistentClient")
    @patch("backend.services.chroma_service.get_settings")
    def test_store_knowledge(self, mock_get_settings, mock_client):
        """Test storing knowledge."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.vectordb.persist_directory = "./test_data/chroma"
        mock_get_settings.return_value = mock_settings

        # Mock collection
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_collection.side_effect = Exception("Not found")
        mock_client_instance.create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        # Create service
        service = ChromaService()

        # Store knowledge
        doc_id = service.store_knowledge(
            content="Test content",
            url="https://example.com/test",
            title="Test Title",
            chunk_index=0,
            total_chunks=1,
            domain="example.com",
        )

        # Verify collection was created and add was called
        assert doc_id.startswith("knowledge_")
        mock_collection.add.assert_called_once()

    @patch("backend.services.chroma_service.chromadb.PersistentClient")
    @patch("backend.services.chroma_service.get_settings")
    def test_delete_knowledge_by_url(self, mock_get_settings, mock_client):
        """Test deleting knowledge by URL."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.vectordb.persist_directory = "./test_data/chroma"
        mock_get_settings.return_value = mock_settings

        # Mock collection with get/delete
        mock_collection = Mock()
        mock_collection.get.return_value = {
            "ids": ["doc_1", "doc_2"],
        }

        mock_client_instance = Mock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        # Create service
        service = ChromaService()

        # Delete by URL
        count = service.delete_knowledge_by_url("https://example.com/test")

        # Verify
        assert count == 2
        mock_collection.delete.assert_called_once_with(ids=["doc_1", "doc_2"])


@pytest.mark.unit
class TestChromaServiceHelpers:
    """Tests for ChromaDB service helper methods."""

    @patch("backend.services.chroma_service.chromadb.PersistentClient")
    @patch("backend.services.chroma_service.get_settings")
    def test_get_or_create_memory_collection(self, mock_get_settings, mock_client):
        """Test getting or creating memory collection."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.vectordb.persist_directory = "./test_data/chroma"
        mock_get_settings.return_value = mock_settings

        # Mock client - collection doesn't exist
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_collection.side_effect = Exception("Not found")
        mock_client_instance.create_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        # Create service
        service = ChromaService()

        # Get or create collection
        collection = service._get_or_create_memory_collection("test_user")

        # Verify collection was created
        mock_client_instance.create_collection.assert_called_once()
        assert collection == mock_collection

    @patch("backend.services.chroma_service.chromadb.PersistentClient")
    @patch("backend.services.chroma_service.get_settings")
    def test_get_or_create_knowledge_collection(self, mock_get_settings, mock_client):
        """Test getting or creating knowledge collection."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.vectordb.persist_directory = "./test_data/chroma"
        mock_get_settings.return_value = mock_settings

        # Mock client - collection exists
        mock_collection = Mock()
        mock_client_instance = Mock()
        mock_client_instance.get_collection.return_value = mock_collection
        mock_client.return_value = mock_client_instance

        # Create service
        service = ChromaService()

        # Get or create collection
        collection = service._get_or_create_knowledge_collection()

        # Verify collection was retrieved, not created
        mock_client_instance.get_collection.assert_called_once()
        mock_client_instance.create_collection.assert_not_called()
        assert collection == mock_collection
