"""SQLite-based knowledge graph for document relationships.

Provides a lightweight graph database using SQLite with nodes and edges tables.
Supports relationship types, weights, and JSON metadata.
"""

import json
import logging
import sqlite3
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RelationType(str, Enum):
    """Standard relationship types for documentation knowledge graph."""

    # Document relationships
    REFERENCES = "references"  # Doc A references Doc B
    DEPENDS_ON = "depends_on"  # Doc A depends on Doc B
    EXTENDS = "extends"  # Doc A extends/builds upon Doc B
    RELATED_TO = "related_to"  # General relationship
    PART_OF = "part_of"  # Doc A is part of Doc B (e.g., section of guide)

    # Concept relationships
    DEFINES = "defines"  # Doc defines a concept
    USES = "uses"  # Doc uses a concept
    IMPLEMENTS = "implements"  # Doc implements a concept

    # Component relationships
    IMPORTS = "imports"  # Component imports another
    COMPOSED_OF = "composed_of"  # Component contains other components
    STYLED_BY = "styled_by"  # Component styled by stylesheet

    # API relationships
    CALLS = "calls"  # API endpoint calls another
    RETURNS = "returns"  # API returns a type
    ACCEPTS = "accepts"  # API accepts a type


class KnowledgeGraph:
    """SQLite-based knowledge graph for document and concept relationships.

    Uses a simple nodes/edges model with JSON metadata support.
    """

    def __init__(self, db_path: str | Path, table_prefix: str = "kg"):
        """Initialize the knowledge graph.

        Args:
            db_path: Path to the SQLite database file.
            table_prefix: Prefix for table names.
        """
        self.db_path = Path(db_path)
        self.table_prefix = table_prefix
        self._conn: sqlite3.Connection | None = None

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_conn()

        # Nodes table - stores documents, concepts, components, etc.
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_prefix}_nodes (
                id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                label TEXT NOT NULL,
                data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Edges table - stores relationships between nodes
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table_prefix}_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES {self.table_prefix}_nodes(id),
                FOREIGN KEY (target_id) REFERENCES {self.table_prefix}_nodes(id),
                UNIQUE(source_id, target_id, relationship_type)
            )
        """)

        # Indexes for efficient queries
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}_nodes_type
            ON {self.table_prefix}_nodes(node_type)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}_edges_source
            ON {self.table_prefix}_edges(source_id)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}_edges_target
            ON {self.table_prefix}_edges(target_id)
        """)
        conn.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}_edges_type
            ON {self.table_prefix}_edges(relationship_type)
        """)

        conn.commit()

    # -------------------------------------------------------------------------
    # Node Operations
    # -------------------------------------------------------------------------

    def add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Add or update a node in the graph.

        Args:
            node_id: Unique identifier for the node.
            node_type: Type of node (document, concept, component, etc.).
            label: Human-readable label.
            data: Optional JSON metadata.

        Returns:
            True if node was created, False if updated.
        """
        conn = self._get_conn()
        data_json = json.dumps(data) if data else None
        now = datetime.now().isoformat()

        try:
            conn.execute(
                f"""
                INSERT INTO {self.table_prefix}_nodes (id, node_type, label, data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (node_id, node_type, label, data_json, now, now),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Node exists, update it
            conn.execute(
                f"""
                UPDATE {self.table_prefix}_nodes
                SET node_type = ?, label = ?, data = ?, updated_at = ?
                WHERE id = ?
            """,
                (node_type, label, data_json, now, node_id),
            )
            conn.commit()
            return False

    def get_node(self, node_id: str) -> dict | None:
        """Get a node by ID.

        Args:
            node_id: Node identifier.

        Returns:
            Node dictionary or None if not found.
        """
        conn = self._get_conn()
        row = conn.execute(
            f"SELECT * FROM {self.table_prefix}_nodes WHERE id = ?",
            (node_id,),
        ).fetchone()

        if row:
            return {
                "id": row["id"],
                "node_type": row["node_type"],
                "label": row["label"],
                "data": json.loads(row["data"]) if row["data"] else None,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        return None

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges.

        Args:
            node_id: Node identifier.

        Returns:
            True if node was removed.
        """
        conn = self._get_conn()

        # Remove edges first
        conn.execute(
            f"""
            DELETE FROM {self.table_prefix}_edges
            WHERE source_id = ? OR target_id = ?
        """,
            (node_id, node_id),
        )

        # Remove node
        cursor = conn.execute(
            f"DELETE FROM {self.table_prefix}_nodes WHERE id = ?",
            (node_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

    def list_nodes(
        self,
        node_type: str | None = None,
        search: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """List nodes with optional filters.

        Args:
            node_type: Filter by node type.
            search: Search in label.
            limit: Maximum results.

        Returns:
            List of node dictionaries.
        """
        conn = self._get_conn()

        query = f"SELECT * FROM {self.table_prefix}_nodes WHERE 1=1"
        params: list[Any] = []

        if node_type:
            query += " AND node_type = ?"
            params.append(node_type)

        if search:
            query += " AND label LIKE ?"
            params.append(f"%{search}%")

        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(query, params).fetchall()

        return [
            {
                "id": row["id"],
                "node_type": row["node_type"],
                "label": row["label"],
                "data": json.loads(row["data"]) if row["data"] else None,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    # -------------------------------------------------------------------------
    # Edge Operations
    # -------------------------------------------------------------------------

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str | RelationType,
        weight: float = 1.0,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Add or update an edge between nodes.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            relationship_type: Type of relationship.
            weight: Edge weight (default 1.0).
            data: Optional JSON metadata.

        Returns:
            True if edge was created, False if updated.
        """
        conn = self._get_conn()

        if isinstance(relationship_type, RelationType):
            relationship_type = relationship_type.value

        data_json = json.dumps(data) if data else None

        try:
            conn.execute(
                f"""
                INSERT INTO {self.table_prefix}_edges
                (source_id, target_id, relationship_type, weight, data)
                VALUES (?, ?, ?, ?, ?)
            """,
                (source_id, target_id, relationship_type, weight, data_json),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Edge exists, update it
            conn.execute(
                f"""
                UPDATE {self.table_prefix}_edges
                SET weight = ?, data = ?
                WHERE source_id = ? AND target_id = ? AND relationship_type = ?
            """,
                (weight, data_json, source_id, target_id, relationship_type),
            )
            conn.commit()
            return False

    def remove_edge(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str | RelationType | None = None,
    ) -> int:
        """Remove edges between nodes.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            relationship_type: Optional relationship type filter.

        Returns:
            Number of edges removed.
        """
        conn = self._get_conn()

        if isinstance(relationship_type, RelationType):
            relationship_type = relationship_type.value

        if relationship_type:
            cursor = conn.execute(
                f"""
                DELETE FROM {self.table_prefix}_edges
                WHERE source_id = ? AND target_id = ? AND relationship_type = ?
            """,
                (source_id, target_id, relationship_type),
            )
        else:
            cursor = conn.execute(
                f"""
                DELETE FROM {self.table_prefix}_edges
                WHERE source_id = ? AND target_id = ?
            """,
                (source_id, target_id),
            )

        conn.commit()
        return cursor.rowcount

    def get_edges(
        self,
        node_id: str,
        direction: str = "both",
        relationship_type: str | RelationType | None = None,
    ) -> list[dict]:
        """Get edges for a node.

        Args:
            node_id: Node identifier.
            direction: "outgoing", "incoming", or "both".
            relationship_type: Optional relationship type filter.

        Returns:
            List of edge dictionaries.
        """
        conn = self._get_conn()

        if isinstance(relationship_type, RelationType):
            relationship_type = relationship_type.value

        results = []

        # Outgoing edges
        if direction in ("both", "outgoing"):
            query = f"""
                SELECT e.*, n.label as target_label, n.node_type as target_type
                FROM {self.table_prefix}_edges e
                JOIN {self.table_prefix}_nodes n ON e.target_id = n.id
                WHERE e.source_id = ?
            """
            params: list[Any] = [node_id]

            if relationship_type:
                query += " AND e.relationship_type = ?"
                params.append(relationship_type)

            rows = conn.execute(query, params).fetchall()
            for row in rows:
                results.append(
                    {
                        "source_id": row["source_id"],
                        "target_id": row["target_id"],
                        "target_label": row["target_label"],
                        "target_type": row["target_type"],
                        "relationship_type": row["relationship_type"],
                        "weight": row["weight"],
                        "data": json.loads(row["data"]) if row["data"] else None,
                        "direction": "outgoing",
                    }
                )

        # Incoming edges
        if direction in ("both", "incoming"):
            query = f"""
                SELECT e.*, n.label as source_label, n.node_type as source_type
                FROM {self.table_prefix}_edges e
                JOIN {self.table_prefix}_nodes n ON e.source_id = n.id
                WHERE e.target_id = ?
            """
            params = [node_id]

            if relationship_type:
                query += " AND e.relationship_type = ?"
                params.append(relationship_type)

            rows = conn.execute(query, params).fetchall()
            for row in rows:
                results.append(
                    {
                        "source_id": row["source_id"],
                        "source_label": row["source_label"],
                        "source_type": row["source_type"],
                        "target_id": row["target_id"],
                        "relationship_type": row["relationship_type"],
                        "weight": row["weight"],
                        "data": json.loads(row["data"]) if row["data"] else None,
                        "direction": "incoming",
                    }
                )

        return results

    # -------------------------------------------------------------------------
    # Graph Queries
    # -------------------------------------------------------------------------

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
        relationship_types: list[str] | None = None,
    ) -> list[dict] | None:
        """Find a path between two nodes using BFS.

        Args:
            source_id: Starting node ID.
            target_id: Target node ID.
            max_depth: Maximum path length.
            relationship_types: Optional filter for relationship types.

        Returns:
            List of edges forming the path, or None if no path found.
        """
        if source_id == target_id:
            return []

        conn = self._get_conn()
        visited = {source_id}
        queue = [(source_id, [])]  # (current_node, path_so_far)

        while queue:
            current, path = queue.pop(0)

            if len(path) >= max_depth:
                continue

            # Get outgoing edges
            query = f"""
                SELECT source_id, target_id, relationship_type, weight, data
                FROM {self.table_prefix}_edges
                WHERE source_id = ?
            """
            params: list[Any] = [current]

            if relationship_types:
                placeholders = ",".join("?" * len(relationship_types))
                query += f" AND relationship_type IN ({placeholders})"
                params.extend(relationship_types)

            rows = conn.execute(query, params).fetchall()

            for row in rows:
                next_node = row["target_id"]

                edge = {
                    "source_id": row["source_id"],
                    "target_id": row["target_id"],
                    "relationship_type": row["relationship_type"],
                    "weight": row["weight"],
                    "data": json.loads(row["data"]) if row["data"] else None,
                }

                if next_node == target_id:
                    return path + [edge]

                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + [edge]))

        return None

    def get_neighbors(
        self,
        node_id: str,
        depth: int = 1,
        relationship_types: list[str] | None = None,
    ) -> dict:
        """Get neighboring nodes up to a certain depth.

        Args:
            node_id: Starting node ID.
            depth: How many hops to traverse.
            relationship_types: Optional filter.

        Returns:
            Dictionary with nodes and edges.
        """
        conn = self._get_conn()
        nodes = {}
        edges = []
        visited = set()

        def traverse(current_id: str, current_depth: int):
            if current_depth > depth or current_id in visited:
                return

            visited.add(current_id)

            # Get node info
            node = self.get_node(current_id)
            if node:
                nodes[current_id] = node

            # Get edges
            node_edges = self.get_edges(
                current_id,
                direction="both",
                relationship_type=None,
            )

            for edge in node_edges:
                if relationship_types and edge["relationship_type"] not in relationship_types:
                    continue

                edges.append(edge)

                # Traverse to connected node
                next_id = (
                    edge["target_id"]
                    if edge["direction"] == "outgoing"
                    else edge["source_id"]
                )
                traverse(next_id, current_depth + 1)

        traverse(node_id, 0)

        return {"nodes": nodes, "edges": edges}

    def get_related_documents(
        self,
        doc_id: str,
        relationship_types: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get documents related to a given document.

        Convenience method for finding related documentation.

        Args:
            doc_id: Document node ID.
            relationship_types: Optional relationship type filter.
            limit: Maximum results.

        Returns:
            List of related document nodes with relationship info.
        """
        edges = self.get_edges(doc_id, direction="both")

        if relationship_types:
            edges = [e for e in edges if e["relationship_type"] in relationship_types]

        # Deduplicate and get unique related nodes
        related = {}
        for edge in edges:
            related_id = (
                edge["target_id"]
                if edge["direction"] == "outgoing"
                else edge["source_id"]
            )
            if related_id not in related:
                node = self.get_node(related_id)
                if node:
                    related[related_id] = {
                        **node,
                        "relationships": [],
                    }
            if related_id in related:
                related[related_id]["relationships"].append(
                    {
                        "type": edge["relationship_type"],
                        "direction": edge["direction"],
                        "weight": edge["weight"],
                    }
                )

        # Sort by number of relationships (more connections = more relevant)
        results = sorted(
            related.values(),
            key=lambda x: len(x["relationships"]),
            reverse=True,
        )

        return results[:limit]

    def get_stats(self) -> dict:
        """Get graph statistics.

        Returns:
            Dictionary with stats.
        """
        conn = self._get_conn()

        total_nodes = conn.execute(
            f"SELECT COUNT(*) FROM {self.table_prefix}_nodes"
        ).fetchone()[0]

        total_edges = conn.execute(
            f"SELECT COUNT(*) FROM {self.table_prefix}_edges"
        ).fetchone()[0]

        # Node types distribution
        node_types = conn.execute(
            f"""
            SELECT node_type, COUNT(*) as count
            FROM {self.table_prefix}_nodes
            GROUP BY node_type
        """
        ).fetchall()

        # Relationship types distribution
        rel_types = conn.execute(
            f"""
            SELECT relationship_type, COUNT(*) as count
            FROM {self.table_prefix}_edges
            GROUP BY relationship_type
        """
        ).fetchall()

        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "node_types": {r["node_type"]: r["count"] for r in node_types},
            "relationship_types": {r["relationship_type"]: r["count"] for r in rel_types},
            "db_path": str(self.db_path),
        }

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
