"""ChromaDB service for memory and knowledge management."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.models.Collection import Collection

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class ChromaService:
    """Service for managing ChromaDB collections."""

    def __init__(self):
        """Initialize ChromaDB client and collections."""
        settings = get_settings()

        # Create persist directory
        persist_dir = Path(settings.vectordb.persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        logger.info(f"ChromaDB initialized at {persist_dir}")

    def _get_or_create_memory_collection(self, user_id: str) -> Collection:
        """Get or create a memory collection for a specific user.

        Args:
            user_id: Unique user identifier

        Returns:
            ChromaDB collection for user's memories
        """
        collection_name = f"memories_{user_id}"
        try:
            collection = self.client.get_collection(name=collection_name)
            logger.debug(f"Retrieved existing collection: {collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"user_id": user_id, "type": "memory"},
            )
            logger.info(f"Created new collection: {collection_name}")

        return collection

    def _get_or_create_knowledge_collection(self) -> Collection:
        """Get or create the global knowledge collection.

        Returns:
            ChromaDB collection for global knowledge
        """
        collection_name = "knowledge_global"
        try:
            collection = self.client.get_collection(name=collection_name)
            logger.debug(f"Retrieved existing collection: {collection_name}")
        except Exception:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"type": "knowledge"},
            )
            logger.info(f"Created new collection: {collection_name}")

        return collection

    # Memory Operations

    def store_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store a memory for a specific user.

        Args:
            user_id: User identifier
            content: Memory content
            metadata: Additional metadata (source, category, etc.)

        Returns:
            Document ID
        """
        collection = self._get_or_create_memory_collection(user_id)

        # Generate unique ID
        doc_id = f"mem_{user_id}_{datetime.now().timestamp()}"

        # Prepare metadata
        doc_metadata = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "source": metadata.get("source", "unknown") if metadata else "unknown",
        }

        # Add optional category
        if metadata and "category" in metadata:
            doc_metadata["category"] = metadata["category"]

        # Store in ChromaDB
        collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[doc_metadata],
        )

        logger.info(f"Stored memory for user {user_id}: {doc_id}")
        return doc_id

    def lookup_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Lookup memories for a specific user using semantic search.

        Args:
            user_id: User identifier
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching memories with content, metadata, and distance
        """
        collection = self._get_or_create_memory_collection(user_id)

        # Check if collection is empty
        if collection.count() == 0:
            logger.debug(f"No memories found for user {user_id}")
            return []

        # Query collection
        results = collection.query(
            query_texts=[query],
            n_results=min(limit, collection.count()),
        )

        # Format results
        memories = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                memory = {
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
                memories.append(memory)

        logger.debug(f"Found {len(memories)} memories for user {user_id}")
        return memories

    # Knowledge Operations

    def store_knowledge(
        self,
        content: str,
        url: str,
        title: str,
        chunk_index: int,
        total_chunks: int,
        domain: str,
    ) -> str:
        """Store knowledge chunk in global collection.

        Args:
            content: Chunk content
            url: Source URL
            title: Page title
            chunk_index: Chunk index (0-based)
            total_chunks: Total number of chunks
            domain: Domain name

        Returns:
            Document ID
        """
        collection = self._get_or_create_knowledge_collection()

        # Generate unique ID
        doc_id = f"knowledge_{domain}_{url.split('/')[-1]}_{chunk_index}"

        # Prepare metadata
        doc_metadata = {
            "url": url,
            "title": title,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "domain": domain,
            "crawl_date": datetime.now().isoformat(),
        }

        # Store in ChromaDB
        collection.add(
            ids=[doc_id],
            documents=[content],
            metadatas=[doc_metadata],
        )

        logger.info(f"Stored knowledge chunk: {doc_id}")
        return doc_id

    def search_knowledge(
        self,
        query: str,
        limit: int = 10,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search global knowledge base.

        Args:
            query: Search query
            limit: Maximum number of results
            domain: Optional domain filter

        Returns:
            List of matching knowledge chunks
        """
        collection = self._get_or_create_knowledge_collection()

        # Check if collection is empty
        if collection.count() == 0:
            logger.debug("Knowledge collection is empty")
            return []

        # Prepare where filter for domain
        where_filter = {"domain": domain} if domain else None

        # Query collection
        results = collection.query(
            query_texts=[query],
            n_results=min(limit, collection.count()),
            where=where_filter,
        )

        # Format results
        knowledge = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                chunk = {
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
                knowledge.append(chunk)

        logger.debug(f"Found {len(knowledge)} knowledge chunks")
        return knowledge

    def delete_knowledge_by_url(self, url: str) -> int:
        """Delete all knowledge chunks from a specific URL.

        Args:
            url: Source URL

        Returns:
            Number of deleted chunks
        """
        collection = self._get_or_create_knowledge_collection()

        # Get all documents with matching URL
        results = collection.get(where={"url": url})

        if not results["ids"]:
            logger.debug(f"No knowledge found for URL: {url}")
            return 0

        # Delete documents
        collection.delete(ids=results["ids"])

        count = len(results["ids"])
        logger.info(f"Deleted {count} knowledge chunks from {url}")
        return count

    def delete_knowledge_by_domain(self, domain: str) -> int:
        """Delete all knowledge chunks from a specific domain.

        Args:
            domain: Domain name

        Returns:
            Number of deleted chunks
        """
        collection = self._get_or_create_knowledge_collection()

        # Get all documents with matching domain
        results = collection.get(where={"domain": domain})

        if not results["ids"]:
            logger.debug(f"No knowledge found for domain: {domain}")
            return 0

        # Delete documents
        collection.delete(ids=results["ids"])

        count = len(results["ids"])
        logger.info(f"Deleted {count} knowledge chunks from domain {domain}")
        return count

    def get_all_knowledge(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all knowledge chunks (for browsing/management).

        Args:
            limit: Optional limit on number of results

        Returns:
            List of all knowledge chunks
        """
        collection = self._get_or_create_knowledge_collection()

        # Get all documents
        results = collection.get(limit=limit)

        # Format results
        knowledge = []
        if results["ids"]:
            for i, doc_id in enumerate(results["ids"]):
                chunk = {
                    "id": doc_id,
                    "content": results["documents"][i],
                    "metadata": results["metadatas"][i],
                }
                knowledge.append(chunk)

        logger.debug(f"Retrieved {len(knowledge)} knowledge chunks")
        return knowledge

    def reset_memory_collection(self, user_id: str) -> None:
        """Delete all memories for a specific user.

        Args:
            user_id: User identifier
        """
        collection_name = f"memories_{user_id}"
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted memory collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection {collection_name}: {e}")

    def reset_knowledge_collection(self) -> None:
        """Delete all knowledge (global)."""
        try:
            self.client.delete_collection(name="knowledge_global")
            logger.info("Deleted knowledge collection")
        except Exception as e:
            logger.warning(f"Failed to delete knowledge collection: {e}")


# Global service instance
_chroma_service: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    """Get or create global ChromaDB service instance."""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
