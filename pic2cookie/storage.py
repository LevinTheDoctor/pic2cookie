"""Where Designs live: a blob store for files and a repository for records.

Blobs go to a folder (`fs`, which may be a mounted volume) or an S3 bucket.
Records go next to the files as design.json, or into MongoDB when a database
URI is configured (ADR-0003).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Protocol

lazy import boto3
lazy import pymongo

from pic2cookie.designs import Design
from pic2cookie.settings import Settings, StorageSettings


class NotFound(KeyError):
    pass


class BlobStore(Protocol):
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None: ...
    def get(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...
    def list(self, prefix: str) -> list[str]: ...
    def delete_prefix(self, prefix: str) -> None: ...


class FsBlobStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise NotFound(key)
        return path

    def put(self, key, data, content_type="application/octet-stream"):
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)

    def get(self, key):
        try:
            return self._path(key).read_bytes()
        except FileNotFoundError as e:
            raise NotFound(key) from e

    def exists(self, key):
        return self._path(key).is_file()

    def list(self, prefix):
        base = self._path(prefix)
        if not base.is_dir():
            return []
        return sorted(str(p.relative_to(self.root)) for p in base.rglob("*") if p.is_file())

    def delete_prefix(self, prefix):
        base = self._path(prefix)
        if base.is_dir():
            for p in sorted(base.rglob("*"), reverse=True):
                p.unlink() if p.is_file() else p.rmdir()
            base.rmdir()


class S3BlobStore:
    def __init__(self, cfg: StorageSettings):
        if not cfg.bucket:
            raise ValueError("PIC2COOKIE_STORAGE__BUCKET is required for S3 storage")
        self.bucket = cfg.bucket
        self.prefix = cfg.prefix.strip("/") + "/" if cfg.prefix.strip("/") else ""
        self.s3 = boto3.client(
            "s3",
            endpoint_url=cfg.endpoint_url,
            region_name=cfg.region,
            aws_access_key_id=cfg.access_key_id,
            aws_secret_access_key=cfg.secret_access_key,
        )
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except self.s3.exceptions.ClientError:
            self.s3.create_bucket(Bucket=self.bucket)  # fails clearly if not allowed

    def put(self, key, data, content_type="application/octet-stream"):
        self.s3.put_object(Bucket=self.bucket, Key=self.prefix + key, Body=data, ContentType=content_type)

    def get(self, key):
        try:
            return self.s3.get_object(Bucket=self.bucket, Key=self.prefix + key)["Body"].read()
        except self.s3.exceptions.NoSuchKey as e:
            raise NotFound(key) from e

    def exists(self, key):
        try:
            self.s3.head_object(Bucket=self.bucket, Key=self.prefix + key)
        except self.s3.exceptions.ClientError:
            return False
        return True

    def list(self, prefix):
        keys = []
        pages = self.s3.get_paginator("list_objects_v2").paginate(
            Bucket=self.bucket, Prefix=self.prefix + prefix
        )
        for page in pages:
            keys += [o["Key"][len(self.prefix) :] for o in page.get("Contents", [])]
        return sorted(keys)

    def delete_prefix(self, prefix):
        keys = self.list(prefix)
        for i in range(0, len(keys), 1000):
            self.s3.delete_objects(
                Bucket=self.bucket,
                Delete={"Objects": [{"Key": self.prefix + k} for k in keys[i : i + 1000]]},
            )


class DesignRepo(Protocol):
    def save(self, design: Design) -> None: ...
    def get(self, design_id: str) -> Design: ...
    def list(self) -> list[Design]: ...
    def delete(self, design_id: str) -> None: ...
    def older_than(self, cutoff: datetime) -> list[str]: ...


class FileDesignRepo:
    """Records as designs/<id>/design.json in the blob store."""

    def __init__(self, blobs: BlobStore):
        self.blobs = blobs

    def save(self, design):
        self.blobs.put(
            f"designs/{design.id}/design.json", design.model_dump_json(indent=2).encode(), "application/json"
        )

    def get(self, design_id):
        return Design.model_validate_json(self.blobs.get(f"designs/{design_id}/design.json"))

    def list(self):
        designs = []
        for key in self.blobs.list("designs/"):
            if key.endswith("/design.json"):
                try:
                    designs.append(Design.model_validate_json(self.blobs.get(key)))
                except NotFound, ValueError:
                    continue  # half-written or deleted meanwhile
        return sorted(designs, key=lambda d: d.updated, reverse=True)

    def delete(self, design_id):
        pass  # the record goes with the Design's files

    def older_than(self, cutoff):
        return [d.id for d in self.list() if d.updated < cutoff]


class MongoDesignRepo:
    def __init__(self, uri: str, name: str):
        self.collection = pymongo.MongoClient(uri, tz_aware=True)[name]["designs"]
        self.collection.create_index([("updated", pymongo.DESCENDING)])

    def save(self, design):
        doc = json.loads(design.model_dump_json())
        doc["updated"] = design.updated  # stored as a date, so it can be queried
        self.collection.replace_one({"_id": design.id}, doc | {"_id": design.id}, upsert=True)

    def get(self, design_id):
        doc = self.collection.find_one({"_id": design_id})
        if doc is None:
            raise NotFound(design_id)
        return Design.model_validate(doc)

    def list(self):
        return [Design.model_validate(d) for d in self.collection.find().sort("updated", -1)]

    def delete(self, design_id):
        self.collection.delete_one({"_id": design_id})

    def older_than(self, cutoff):
        return [d["_id"] for d in self.collection.find({"updated": {"$lt": cutoff}}, {"_id": 1})]


def blob_store(cfg: Settings) -> BlobStore:
    return S3BlobStore(cfg.storage) if cfg.storage.type == "s3" else FsBlobStore(cfg.storage.path)


def design_repo(cfg: Settings, blobs: BlobStore) -> DesignRepo:
    if cfg.database.uri:
        return MongoDesignRepo(cfg.database.uri, cfg.database.name)
    return FileDesignRepo(blobs)
