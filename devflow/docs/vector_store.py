"""SQLite-based vector store using sqlite-vec.

sqlite-vec is a pure-C SQLite extension for vector similarity search.
It stores vectors efficiently and provides fast nearest-neighbor queries.
"""

import json
import logging
import sqlite3
import struct
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Embedding dimensions for the default model (bge-small-en-v1.5)
DEFAULT_DIMENSIONS = 384


def _serialize_vector(vector: list[float]) -> bytes:
    """Serialize a vector to bytes for sqlite-vec.

    sqlite-vec expects vectors as raw bytes in little-endian float32 format.

    Args:
        vector: List of floats.

    Returns:
        Bytes representation.
    """
    return struct.pack(f"<{len(vector)}f", *vector)


def _deserialize_vector(data: bytes) -> list[float]:
    """Deserialize bytes back to a vector.

    Args:
        data: Bytes representation.

    Returns:
        List of floats.
    """
    count = len(data) // 4  # 4 bytes per float32
    return list(struct.unpack(f"<{count}f", data))


class VectorStore:
    """SQLite-based vector store for semantic document search.

    Uses sqlite-vec extension for efficient vector similarity queries.
    Falls back to brute-force search if sqlite-vec is not available.
    """

    def __init__(
        self,
        db_path: str | Path,
        dimensions: int = DEFAULT_DIMENSIONS,
        table_prefix: str = "docs",
    ):
        """Initialize the vector store.

        Args:
            db_path: Path to the SQLite database file.
            dimensions: Vector dimensions (must match embedding model).
            table_prefix: Prefix for table names.
        """
        self.db_path = Path(db_path)
        self.dimensions = dimensions
        self.table_prefix = table_prefix
        self._conn: sqlite3.Connection | None = None
        self._has_vec_extension = False

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._try_load_vec_extension()
        return self._conn

    def _try_load_vec_extension(self):
        """Try to load the sqlite-vec extension."""
        conn = self._conn
        if conn is None:
            return

        try:
            # Enable extension loading
            conn.enable_load_extension(True)

            # Try to load sqlite-vec
            try:
                import sqlite_vec

                sqlite_vec.load(conn)
                self._has_vec_extension = True
                logger.info("sqlite-vec extension loaded successfully")
            except ImportError:
                # Try loading as a shared library
                try:
                    conn.load_extension("vec0")
                    self._has_vec_extension = True
                    logger.info("sqlite-vec extension loaded from system")
                except sqlite3.OperationalError:
                    logger.warning(
                        "sqlite-vec not available, using fallback similarity search"
                    )
                    self._has_vec_extension = False
        except Exception as e:
            logger.warning(f"Could not enable extensions: {e}")
            self._has_vec_extension = False

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()

        # Main documents table (stores metadata and chunks)
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_prefix}_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding BLOB,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(doc_id, chunk_index)
            )
        """)

        # Create index on doc_id for fast lookups
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}_doc_id
            ON {self.table_prefix}_chunks(doc_id)
        """)

        # If sqlite-vec is available, create virtual table for vector search
        if self._has_vec_extension:
            try:
                conn.execute(f"""
                    CREATE VIRTUAL TABLE IF NOT EXISTS {self.table_prefix}_vec
                    USING vec0(embedding float[{self.dimensions}])
                """)
                logger.info("Created vector virtual table")
            except sqlite3.OperationalError as e:
                logger.warning(f"Could not create vec table: {e}")
                self._has_vec_extension = False

        conn.commit()

    def add_document(
        self,
        doc_id: str,
        chunks: list[tuple[str, list[float]]],
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Add a document's chunks and embeddings to the store.

        Args:
            doc_id: Unique document identifier.
            chunks: List of (chunk_text, embedding) tuples.
            metadata: Optional metadata to store with each chunk.

        Returns:
            Number of chunks added.
        """
        conn = self._get_conn()

        # First, remove any existing chunks for this document
        self.remove_document(doc_id)

        metadata_json = json.dumps(metadata) if metadata else None

        for idx, (chunk_text, embedding) in enumerate(chunks):
            # Serialize embedding
            embedding_bytes = _serialize_vector(embedding)

            # Insert into chunks table
            cursor = conn.execute(
                f"""
                INSERT INTO {self.table_prefix}_chunks
                (doc_id, chunk_index, chunk_text, embedding, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (doc_id, idx, chunk_text, embedding_bytes, metadata_json),
            )

            # If vec extension available, add to vector index
            if self._has_vec_extension:
                rowid = cursor.lastrowid
                conn.execute(
                    f"""
                    INSERT INTO {self.table_prefix}_vec(rowid, embedding)
                    VALUES (?, ?)
                """,
                    (rowid, embedding_bytes),
                )

        conn.commit()
        return len(chunks)

    def remove_document(self, doc_id: str) -> int:
        """Remove all chunks for a document.

        Args:
            doc_id: Document identifier.

        Returns:
            Number of chunks removed.
        """
        conn = self._get_conn()

        # Get rowids before deletion (for vec table)
        if self._has_vec_extension:
            rows = conn.execute(
                f"SELECT id FROM {self.table_prefix}_chunks WHERE doc_id = ?",
                (doc_id,),
            ).fetchall()
            for row in rows:
                conn.execute(
                    f"DELETE FROM {self.table_prefix}_vec WHERE rowid = ?",
                    (row["id"],),
                )

        cursor = conn.execute(
            f"DELETE FROM {self.table_prefix}_chunks WHERE doc_id = ?",
            (doc_id,),
        )
        conn.commit()
        return cursor.rowcount

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        doc_ids: list[str] | None = None,
    ) -> list[dict]:
        """Search for similar document chunks.

        Args:
            query_embedding: Query vector.
            limit: Maximum results to return.
            doc_ids: Optional filter to specific documents.

        Returns:
            List of results with doc_id, chunk_text, similarity, metadata.
        """
        conn = self._get_conn()
        query_bytes = _serialize_vector(query_embedding)

        if self._has_vec_extension:
            return self._search_vec(conn, query_bytes, limit, doc_ids)
        else:
            return self._search_brute_force(conn, query_embedding, limit, doc_ids)

    def _search_vec(
        self,
        conn: sqlite3.Connection,
        query_bytes: bytes,
        limit: int,
        doc_ids: list[str] | None,
    ) -> list[dict]:
        """Search using sqlite-vec extension."""
        # Get candidates from vector index
        vec_results = conn.execute(
            f"""
            SELECT rowid, distance
            FROM {self.table_prefix}_vec
            WHERE embedding MATCH ?
            ORDER BY distance
            LIMIT ?
        """,
            (query_bytes, limit * 2),  # Get extra for filtering
        ).fetchall()

        if not vec_results:
            return []

        # Get chunk details
        rowids = [r["rowid"] for r in vec_results]
        distances = {r["rowid"]: r["distance"] for r in vec_results}

        placeholders = ",".join("?" * len(rowids))
        query = f"""
            SELECT id, doc_id, chunk_index, chunk_text, metadata
            FROM {self.table_prefix}_chunks
            WHERE id IN ({placeholders})
        """
        rows = conn.execute(query, rowids).fetchall()

        results = []
        for row in rows:
            if doc_ids and row["doc_id"] not in doc_ids:
                continue

            # Convert distance to similarity (sqlite-vec uses L2 distance)
            distance = distances.get(row["id"], 0)
            similarity = 1.0 / (1.0 + distance)

            results.append(
                {
                    "doc_id": row["doc_id"],
                    "chunk_index": row["chunk_index"],
                    "chunk_text": row["chunk_text"],
                    "similarity": similarity,
                    "metadata": json.loads(row["metadata"])
                    if row["metadata"]
                    else None,
                }
            )

        # Sort by similarity and limit
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def _search_brute_force(
        self,
        conn: sqlite3.Connection,
        query_embedding: list[float],
        limit: int,
        doc_ids: list[str] | None,
    ) -> list[dict]:
        """Fallback brute-force similarity search."""
        import numpy as np

        query = f"""
            SELECT id, doc_id, chunk_index, chunk_text, embedding, metadata
            FROM {self.table_prefix}_chunks
        """
        params: list[Any] = []

        if doc_ids:
            placeholders = ",".join("?" * len(doc_ids))
            query += f" WHERE doc_id IN ({placeholders})"
            params.extend(doc_ids)

        rows = conn.execute(query, params).fetchall()

        # Compute similarities
        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)

        results = []
        for row in rows:
            if row["embedding"]:
                doc_vec = np.array(_deserialize_vector(row["embedding"]))
                doc_norm = np.linalg.norm(doc_vec)
                if doc_norm > 0 and query_norm > 0:
                    similarity = float(np.dot(query_vec, doc_vec) / (query_norm * doc_norm))
                else:
                    similarity = 0.0

                results.append(
                    {
                        "doc_id": row["doc_id"],
                        "chunk_index": row["chunk_index"],
                        "chunk_text": row["chunk_text"],
                        "similarity": similarity,
                        "metadata": json.loads(row["metadata"])
                        if row["metadata"]
                        else None,
                    }
                )

        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def get_document_chunks(self, doc_id: str) -> list[dict]:
        """Get all chunks for a document.

        Args:
            doc_id: Document identifier.

        Returns:
            List of chunk info dictionaries.
        """
        conn = self._get_conn()
        rows = conn.execute(
            f"""
            SELECT chunk_index, chunk_text, metadata
            FROM {self.table_prefix}_chunks
            WHERE doc_id = ?
            ORDER BY chunk_index
        """,
            (doc_id,),
        ).fetchall()

        return [
            {
                "chunk_index": row["chunk_index"],
                "chunk_text": row["chunk_text"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
            }
            for row in rows
        ]

    def get_stats(self) -> dict:
        """Get store statistics.

        Returns:
            Dictionary with stats.
        """
        conn = self._get_conn()

        total_chunks = conn.execute(
            f"SELECT COUNT(*) FROM {self.table_prefix}_chunks"
        ).fetchone()[0]

        total_docs = conn.execute(
            f"SELECT COUNT(DISTINCT doc_id) FROM {self.table_prefix}_chunks"
        ).fetchone()[0]

        return {
            "total_chunks": total_chunks,
            "total_documents": total_docs,
            "dimensions": self.dimensions,
            "has_vec_extension": self._has_vec_extension,
            "db_path": str(self.db_path),
        }

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
