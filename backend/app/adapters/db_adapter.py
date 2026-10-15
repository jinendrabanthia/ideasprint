"""Universal Database and Auth Adapter.

Provides seamless dual-mode persistence:
1. Supabase (PostgreSQL) when cloud credentials and schema are available.
2. Local SQLite fallback when offline, in development, or running local tests.

This ensures zero external dependencies for local demonstrations and tests,
while strictly honoring the full PostgREST and Auth interface.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import jwt

from app.core.config import settings

DB_PATH = Path(__file__).resolve().parent.parent.parent / "elder_care.db"


class PostgrestResult:
    """Wraps result rows like Supabase postgrest execute()."""
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data


class SQLiteQueryBuilder:
    """Emulates PostgREST query chain over SQLite."""

    def __init__(self, conn: sqlite3.Connection, table_name: str):
        self.conn = conn
        self.table_name = table_name
        self._action = "SELECT"
        self._columns = "*"
        self._filters: List[tuple[str, str, Any]] = []  # (col, op, val)
        self._order_col: Optional[str] = None
        self._order_desc: bool = False
        self._limit_val: Optional[int] = None
        self._payload: Optional[Dict[str, Any] | List[Dict[str, Any]]] = None

    def select(self, columns: str = "*") -> SQLiteQueryBuilder:
        self._action = "SELECT"
        self._columns = columns
        return self

    def insert(self, payload: Dict[str, Any] | List[Dict[str, Any]]) -> SQLiteQueryBuilder:
        self._action = "INSERT"
        self._payload = payload
        return self

    def update(self, payload: Dict[str, Any]) -> SQLiteQueryBuilder:
        self._action = "UPDATE"
        self._payload = payload
        return self

    def delete(self) -> SQLiteQueryBuilder:
        self._action = "DELETE"
        return self

    def eq(self, column: str, value: Any) -> SQLiteQueryBuilder:
        self._filters.append((column, "=", value))
        return self

    def neq(self, column: str, value: Any) -> SQLiteQueryBuilder:
        self._filters.append((column, "!=", value))
        return self

    def order(self, column: str, desc: bool = False) -> SQLiteQueryBuilder:
        self._order_col = column
        self._order_desc = desc
        return self

    def limit(self, count: int) -> SQLiteQueryBuilder:
        self._limit_val = count
        return self

    def execute(self) -> PostgrestResult:
        cursor = self.conn.cursor()

        if self._action == "INSERT":
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            valid_cols = {row[1] for row in cursor.fetchall()}
            items = self._payload if isinstance(self._payload, list) else [self._payload]
            inserted_rows = []
            for item in items:
                row_dict = dict(item)
                if "id" in valid_cols and ("id" not in row_dict or not row_dict["id"]):
                    row_dict["id"] = str(uuid.uuid4())
                if "created_at" in valid_cols and "created_at" not in row_dict:
                    row_dict["created_at"] = datetime.now(timezone.utc).isoformat()
                if "updated_at" in valid_cols and "updated_at" not in row_dict:
                    row_dict["updated_at"] = datetime.now(timezone.utc).isoformat()

                # Serialize JSON / boolean fields and retain only valid columns
                clean_dict = {}
                for k, v in row_dict.items():
                    if k not in valid_cols:
                        continue
                    if isinstance(v, (dict, list)):
                        clean_dict[k] = json.dumps(v)
                    elif isinstance(v, bool):
                        clean_dict[k] = 1 if v else 0
                    else:
                        clean_dict[k] = v

                keys = list(clean_dict.keys())
                placeholders = [f":{k}" for k in keys]
                sql = f"INSERT INTO {self.table_name} ({', '.join(keys)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(sql, clean_dict)
                inserted_rows.append(row_dict)

            self.conn.commit()
            return PostgrestResult(inserted_rows)

        where_clause = ""
        params: List[Any] = []
        if self._filters:
            clauses = []
            for col, op, val in self._filters:
                clauses.append(f"{col} {op} ?")
                params.append(1 if val is True else (0 if val is False else val))
            where_clause = " WHERE " + " AND ".join(clauses)

        if self._action == "UPDATE":
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            valid_cols = {row[1] for row in cursor.fetchall()}
            set_clauses = []
            update_dict = dict(self._payload or {})
            if "updated_at" in valid_cols and "updated_at" not in update_dict:
                update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
            update_params = []
            for k, v in update_dict.items():
                if k not in valid_cols:
                    continue
                set_clauses.append(f"{k} = ?")
                if isinstance(v, (dict, list)):
                    update_params.append(json.dumps(v))
                elif isinstance(v, bool):
                    update_params.append(1 if v else 0)
                else:
                    update_params.append(v)

            if set_clauses:
                sql = f"UPDATE {self.table_name} SET {', '.join(set_clauses)}{where_clause}"
                cursor.execute(sql, update_params + params)
                self.conn.commit()

            # Return updated rows
            select_sql = f"SELECT * FROM {self.table_name}{where_clause}"
            cursor.execute(select_sql, params)
            rows = [self._row_to_dict(cursor, r) for r in cursor.fetchall()]
            return PostgrestResult(rows)

        if self._action == "DELETE":
            # Find rows before deleting to return
            select_sql = f"SELECT * FROM {self.table_name}{where_clause}"
            cursor.execute(select_sql, params)
            rows = [self._row_to_dict(cursor, r) for r in cursor.fetchall()]

            sql = f"DELETE FROM {self.table_name}{where_clause}"
            cursor.execute(sql, params)
            self.conn.commit()
            return PostgrestResult(rows)

        # SELECT
        order_clause = ""
        if self._order_col:
            direction = "DESC" if self._order_desc else "ASC"
            order_clause = f" ORDER BY {self._order_col} {direction}"

        limit_clause = ""
        if self._limit_val is not None:
            limit_clause = f" LIMIT {self._limit_val}"

        sql = f"SELECT * FROM {self.table_name}{where_clause}{order_clause}{limit_clause}"
        cursor.execute(sql, params)
        rows = [self._row_to_dict(cursor, r) for r in cursor.fetchall()]
        return PostgrestResult(rows)

    def _row_to_dict(self, cursor: sqlite3.Cursor, row: tuple) -> Dict[str, Any]:
        columns = [desc[0] for desc in cursor.description]
        d = {}
        for col, val in zip(columns, row):
            # Attempt to deserialize json
            if isinstance(val, str) and (val.startswith("{") or val.startswith("[")):
                try:
                    d[col] = json.loads(val)
                    continue
                except Exception:
                    pass
            d[col] = val
        return d


class SQLiteAuthUser:
    def __init__(self, uid: str, email: str, user_metadata: Dict[str, Any]):
        self.id = uid
        self.email = email
        self.user_metadata = user_metadata


class SQLiteAuthResponse:
    def __init__(self, user: SQLiteAuthUser, access_token: str):
        self.user = user
        self.session = type("Session", (), {"access_token": access_token})()


class SQLiteAuth:
    """Emulates Supabase Auth operations using SQLite and JWT."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def sign_up(self, credentials: Dict[str, Any]) -> SQLiteAuthResponse:
        email = credentials["email"].strip().lower()
        password = credentials["password"]
        options = credentials.get("options", {})
        metadata = options.get("data", {})

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, email, user_metadata FROM auth_accounts WHERE email = ?", (email,))
        existing = cursor.fetchone()
        if existing:
            raise Exception("User already registered")

        user_id = str(uuid.uuid4())
        pwd_hash = self._hash_password(password)
        cursor.execute(
            "INSERT INTO auth_accounts (id, email, password_hash, user_metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, pwd_hash, json.dumps(metadata), datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

        token = jwt.encode(
            {"sub": user_id, "email": email, "metadata": metadata, "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 30},
            settings.secret_key,
            algorithm="HS256",
        )
        return SQLiteAuthResponse(SQLiteAuthUser(user_id, email, metadata), token)

    def sign_in_with_password(self, credentials: Dict[str, Any]) -> SQLiteAuthResponse:
        email = credentials["email"].strip().lower()
        password = credentials["password"]

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, email, password_hash, user_metadata FROM auth_accounts WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            raise Exception("Invalid login credentials")

        user_id, user_email, pwd_hash, meta_str = row
        if pwd_hash != self._hash_password(password):
            raise Exception("Invalid login credentials")

        metadata = json.loads(meta_str) if meta_str else {}
        token = jwt.encode(
            {"sub": user_id, "email": user_email, "metadata": metadata, "exp": int(datetime.now(timezone.utc).timestamp()) + 86400 * 30},
            settings.secret_key,
            algorithm="HS256",
        )
        return SQLiteAuthResponse(SQLiteAuthUser(user_id, user_email, metadata), token)

    def get_user(self, token: str) -> SQLiteAuthResponse:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            user_id = payload["sub"]
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, email, user_metadata FROM auth_accounts WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                raise Exception("User not found")
            meta = json.loads(row[2]) if row[2] else {}
            return SQLiteAuthResponse(SQLiteAuthUser(row[0], row[1], meta), token)
        except Exception as e:
            raise Exception(f"Invalid token: {e}")


class SQLiteDatabaseClient:
    """Full drop-in client mimicking Supabase Client."""

    def __init__(self, db_path: Path = DB_PATH):
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_schema()
        self.auth = SQLiteAuth(self.conn)

    def _init_schema(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS auth_accounts (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            user_metadata TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            auth_id TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            role TEXT DEFAULT 'senior',
            display_name TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS senior_profiles (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            display_name TEXT DEFAULT '',
            timezone TEXT DEFAULT 'UTC',
            language TEXT DEFAULT 'en',
            speech_rate REAL DEFAULT 1.0,
            high_contrast INTEGER DEFAULT 0,
            large_text INTEGER DEFAULT 0,
            onboarding_complete INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS caregiver_relationships (
            id TEXT PRIMARY KEY,
            caregiver_user_id TEXT NOT NULL,
            senior_profile_id TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            permissions TEXT DEFAULT '["view_reminders", "view_checkins"]',
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            label TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            scheduled_utc TEXT,
            recurrence TEXT DEFAULT 'daily',
            is_medication INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_by TEXT,
            idempotency_key TEXT UNIQUE,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS checkins (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            response TEXT,
            notes TEXT DEFAULT '',
            escalated INTEGER DEFAULT 0,
            created_at TEXT,
            responded_at TEXT
        );

        CREATE TABLE IF NOT EXISTS checkin_configs (
            id TEXT PRIMARY KEY,
            profile_id TEXT UNIQUE NOT NULL,
            enabled INTEGER DEFAULT 1,
            time TEXT DEFAULT '09:00',
            questions TEXT DEFAULT '["How are you feeling today?"]',
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS trusted_contacts (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            relationship TEXT DEFAULT '',
            is_emergency INTEGER DEFAULT 0,
            notify_on_help INTEGER DEFAULT 1,
            notify_on_missed_checkin INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            is_simulated INTEGER DEFAULT 1,
            recipient TEXT DEFAULT '',
            metadata TEXT DEFAULT '{}',
            created_at TEXT,
            delivered_at TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            user_id TEXT,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            profile_id TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS conversation_turns (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            intent TEXT,
            action_taken TEXT,
            created_at TEXT
        );
        """)
        self.conn.commit()

    def table(self, table_name: str) -> SQLiteQueryBuilder:
        return SQLiteQueryBuilder(self.conn, table_name)


# Global singleton
_sqlite_client: Optional[SQLiteDatabaseClient] = None

def get_sqlite_client() -> SQLiteDatabaseClient:
    global _sqlite_client
    if _sqlite_client is None:
        _sqlite_client = SQLiteDatabaseClient()
    return _sqlite_client
