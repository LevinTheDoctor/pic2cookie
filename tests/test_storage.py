from datetime import timedelta

import mongomock
import pytest
from moto import mock_aws

from pic2cookie.designs import Design, Source, now
from pic2cookie.settings import StorageSettings
from pic2cookie.storage import FileDesignRepo, FsBlobStore, MongoDesignRepo, NotFound, S3BlobStore


def design(design_id: str, age_days: int = 0) -> Design:
    when = now() - timedelta(days=age_days)
    return Design(
        id=design_id,
        name=design_id,
        created=when,
        updated=when,
        source=Source(filename="x.svg", kind="svg", key="source.svg"),
    )


def exercise_blobs(store):
    store.put("designs/a/x.txt", b"hello")
    store.put("designs/a/sub/y.txt", b"world")
    store.put("designs/b/z.txt", b"!")
    assert store.get("designs/a/x.txt") == b"hello"
    assert store.exists("designs/a/x.txt") and not store.exists("designs/a/nope")
    assert store.list("designs/a/") == ["designs/a/sub/y.txt", "designs/a/x.txt"]
    store.delete_prefix("designs/a/")
    assert store.list("designs/a/") == []
    assert store.list("designs/") == ["designs/b/z.txt"]
    with pytest.raises(NotFound):
        store.get("designs/a/x.txt")


def test_fs_blobs(tmp_path):
    store = FsBlobStore(tmp_path)
    exercise_blobs(store)
    with pytest.raises(NotFound):
        store.get("../outside")


@mock_aws
def test_s3_blobs_create_their_bucket():
    store = S3BlobStore(StorageSettings(type="s3", bucket="cookies", prefix="p2c", region="us-east-1"))
    exercise_blobs(store)
    keys = [o["Key"] for o in store.s3.list_objects_v2(Bucket="cookies")["Contents"]]
    assert keys == ["p2c/designs/b/z.txt"]


def exercise_repo(repo):
    repo.save(design("new"))
    repo.save(design("old", age_days=40))
    assert [d.id for d in repo.list()] == ["new", "old"]
    assert repo.get("old").name == "old"
    assert repo.older_than(now() - timedelta(days=30)) == ["old"]
    with pytest.raises(NotFound):
        repo.get("missing")


def test_file_repo(tmp_path):
    exercise_repo(FileDesignRepo(FsBlobStore(tmp_path)))


def test_mongo_repo(monkeypatch):
    monkeypatch.setattr("pymongo.MongoClient", mongomock.MongoClient)
    repo = MongoDesignRepo("mongodb://localhost", "test")
    exercise_repo(repo)
    repo.delete("old")
    assert [d.id for d in repo.list()] == ["new"]
