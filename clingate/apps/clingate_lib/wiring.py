"""Composition root helpers: pick memory or AWS adapters from Settings."""

from __future__ import annotations

from .aws import S3RawStore, SqsQueue
from .config import Settings
from .memory import MemoryQueue, MemoryRawStore, NullQueue, NullRawStore
from .ports import RawStore, WorkQueue
from .repo import Repository
from .repo_memory import MemoryRepository


def build_store(s: Settings) -> RawStore:
    if s.backend == "null":
        return NullRawStore()
    return MemoryRawStore() if s.backend == "memory" else S3RawStore(s.raw_bucket)


def build_queue(s: Settings, url: str) -> WorkQueue:
    if s.backend == "null":
        return NullQueue()
    return MemoryQueue() if s.backend == "memory" else SqsQueue(url)


def build_repo(s: Settings) -> Repository:
    if s.db_dsn:
        from .repo_pg import PgRepository

        return PgRepository(s.db_dsn)
    if s.backend == "memory":
        return MemoryRepository()
    raise RuntimeError("CLINGATE_DB_DSN is required with the aws backend")
