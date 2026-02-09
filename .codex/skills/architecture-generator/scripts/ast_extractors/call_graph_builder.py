#!/usr/bin/env python3
"""
Call graph builder for tracking function call relationships.

Builds and manages a call graph showing which functions call which.
"""

import sqlite3
from typing import List, Dict, Set
from pathlib import Path


class CallGraphBuilder:
    """Build and manage call graph"""

    def __init__(self, db_path: str):
        """
        Initialize call graph builder.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database schema for call graph"""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_graph (
                caller_id INTEGER,
                callee_name TEXT NOT NULL,
                line_number INTEGER,
                FOREIGN KEY (caller_id) REFERENCES symbols(id)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_graph_caller ON call_graph(caller_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_graph_callee ON call_graph(callee_name)")

        self.conn.commit()

    def add_call(self, caller_id: int, callee_name: str, line_number: int):
        """
        Add a function call to the graph.

        Args:
            caller_id: ID of the calling function
            callee_name: Name of the function being called
            line_number: Line number of the call
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO call_graph (caller_id, callee_name, line_number) VALUES (?, ?, ?)",
            (caller_id, callee_name, line_number)
        )
        self.conn.commit()

    def get_callees(self, caller_id: int) -> List[str]:
        """
        Get all functions called by a function.

        Args:
            caller_id: ID of the calling function

        Returns:
            List of function names
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT DISTINCT callee_name FROM call_graph WHERE caller_id = ?",
            (caller_id,)
        )
        return [row[0] for row in cursor.fetchall()]

    def get_callers(self, callee_name: str) -> List[int]:
        """
        Get all functions that call a given function.

        Args:
            callee_name: Name of the function being called

        Returns:
            List of caller function IDs
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT DISTINCT caller_id FROM call_graph WHERE callee_name = ?",
            (callee_name,)
        )
        return [row[0] for row in cursor.fetchall()]

    def get_all_calls(self) -> List[Dict]:
        """
        Get all function calls in the graph.

        Returns:
            List of call information dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT caller_id, callee_name, line_number FROM call_graph")

        return [
            {
                'caller_id': row[0],
                'callee_name': row[1],
                'line_number': row[2]
            }
            for row in cursor.fetchall()
        ]

    def build_transitive_closure(self) -> Dict[int, Set[str]]:
        """
        Build transitive closure of call graph.

        Computes all reachable functions for each function.

        Returns:
            Dictionary mapping function IDs to sets of reachable function names
        """
        # Build adjacency list
        graph = {}
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT caller_id FROM call_graph")

        for row in cursor.fetchall():
            caller_id = row[0]
            callees = self.get_callees(caller_id)
            graph[caller_id] = set(callees)

        # Compute transitive closure using fixed-point iteration
        closure = {}
        changed = True

        # Initialize closure with direct calls
        for caller_id, callees in graph.items():
            closure[caller_id] = set(callees)

        # Iteratively expand until no changes
        while changed:
            changed = False
            for caller_id in closure:
                current_size = len(closure[caller_id])
                # Add callees of callees
                new_callees = set()
                for callee in list(closure[caller_id]):
                    # Find caller IDs for this callee name
                    cursor.execute(
                        "SELECT id FROM symbols WHERE name = ? AND kind = 'function'",
                        (callee,)
                    )
                    for row in cursor.fetchall():
                        callee_id = row[0]
                        if callee_id in closure:
                            new_callees.update(closure[callee_id])

                closure[caller_id].update(new_callees)
                if len(closure[caller_id]) > current_size:
                    changed = True

        return closure

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
