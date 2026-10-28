import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PIC2COOKIE_STORAGE__PATH", str(tmp_path / "data"))
    monkeypatch.setenv("PIC2COOKIE_FRONTEND_DIR", str(tmp_path / "no-frontend"))
    from pic2cookie import jobs, service, settings

    for cached in (settings.settings, service.service, jobs.executor):
        cached.cache_clear()
    from pic2cookie.api import app

    with TestClient(app) as c:
        yield c
    for cached in (settings.settings, service.service, jobs.executor):
        cached.cache_clear()


def wait(client, job):
    for _ in range(200):
        job = client.get(f"/api/jobs/{job['id']}").json()
        if job["status"] in ("done", "failed"):
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def upload(client, fixture_bytes, name="donut_lines.svg", filename=None):
    files = {"file": (filename or name, fixture_bytes(name), "image/svg+xml")}
    res = client.post("/api/designs", files=files)
    assert res.status_code == 201, res.text
    body = res.json()
    assert wait(client, body["job"])["status"] == "done"
    return client.get(f"/api/designs/{body['design']['id']}").json()


def test_meta(client):
    meta = client.get("/api/meta").json()
    assert meta["default_printer"] == "a1mini"
    assert {p["id"] for p in meta["printers"]} >= {"a1mini", "p2s"}
    assert meta["defaults"]["cutter"]["size"] == 80


def test_design_lifecycle(client, fixture_bytes):
    design = upload(client, fixture_bytes)
    assert design["status"] == "ready"
    assert design["name"] == "donut_lines"
    assert design["result"]["estimate"]["grams"] > 0
    features = {f["id"]: f for f in design["result"]["features"]}
    assert features["r3"]["role"] == "ignore"

    res = client.patch(
        f"/api/designs/{design['id']}",
        json={"roles": {"r3": "hole"}, "cutter": {"size": 70}, "printer": "p2s"},
    )
    assert res.status_code == 200
    wait(client, res.json()["job"])
    changed = client.get(f"/api/designs/{design['id']}").json()
    assert changed["roles"] == {"r3": "hole"}
    assert changed["result"]["dimensions"]["width"] < design["result"]["dimensions"]["width"]

    for name in ("cutter.stl", "cutter.3mf", "cutter.bambu.3mf", "picture.svg", "roles.svg"):
        res = client.get(f"/api/designs/{design['id']}/files/{name}?download=true")
        assert res.status_code == 200, name
        assert "attachment" in res.headers["content-disposition"]
    assert client.get(f"/api/designs/{design['id']}/files/design.json").status_code == 404
    assert client.get(f"/api/designs/{design['id']}/files/..%2Fx").status_code == 404

    copy = client.post(f"/api/designs/{design['id']}/duplicate").json()
    assert copy["name"].endswith("(copy)") and copy["result"] is not None
    assert client.get(f"/api/designs/{copy['id']}/files/cutter.stl").status_code == 200
    assert len(client.get("/api/designs").json()) == 2

    assert client.delete(f"/api/designs/{design['id']}").status_code == 204
    assert client.get(f"/api/designs/{design['id']}").status_code == 404
    assert len(client.get("/api/designs").json()) == 1


def test_png_upload_is_traced(client, donut_png):
    res = client.post("/api/designs", files={"file": ("donut.png", donut_png, "image/png")})
    body = res.json()
    assert wait(client, body["job"])["status"] == "done"
    design = client.get(f"/api/designs/{body['design']['id']}").json()
    assert design["source"]["kind"] == "raster"
    roles = [f["role"] for f in design["result"]["features"]]
    assert roles.count("hole") == 1
    svg = client.get(f"/api/designs/{design['id']}/files/picture.svg").text
    assert svg.startswith("<svg")


def test_changing_tracing_resets_roles(client, donut_png):
    body = client.post("/api/designs", files={"file": ("d.png", donut_png, "image/png")}).json()
    wait(client, body["job"])
    did = body["design"]["id"]
    client.patch(f"/api/designs/{did}?generate=false", json={"roles": {"r1": "imprint"}})
    res = client.patch(f"/api/designs/{did}?generate=false", json={"trace": {"tolerance": 0.5}})
    assert res.json()["design"]["roles"] == {}


def test_bad_uploads(client):
    res = client.post("/api/designs", files={"file": ("x.txt", b"hello", "text/plain")})
    assert res.status_code == 422
    assert res.json()["detail"]["code"] == "upload_type"
    res = client.post(
        "/api/designs",
        files={"file": ("x.svg", b"<svg xmlns='http://www.w3.org/2000/svg'/>", "image/svg+xml")},
    )
    job = wait(client, res.json()["job"])
    assert job["status"] == "failed"
    design = client.get(f"/api/designs/{res.json()['design']['id']}").json()
    assert design["status"] == "failed"
    assert design["error"]["code"] == "no_ink" and "Ink" in design["error"]["text"]


def test_unknown_printer(client, fixture_bytes):
    design = upload(client, fixture_bytes, "hi.svg")
    res = client.patch(f"/api/designs/{design['id']}", json={"printer": "nope"})
    assert res.status_code == 422


def test_retention_sweep(client, fixture_bytes, monkeypatch):
    from pic2cookie.designs import now
    from pic2cookie.service import service

    design = upload(client, fixture_bytes, "hi.svg")
    svc = service()
    old = svc.get(design["id"]).model_copy(update={"updated": now() - timedelta(days=40)})
    svc.repo.save(old)
    monkeypatch.setattr(svc.cfg.retention, "days", 30)
    assert svc.sweep() == [design["id"]]
    assert client.get("/api/designs").json() == []


def test_coaster_design(client, fixture_bytes):
    files = {"file": ("hi.svg", fixture_bytes("hi.svg"), "image/svg+xml")}
    res = client.post("/api/designs", files=files, data={"product": "coaster"})
    assert res.status_code == 201, res.text
    body = res.json()
    assert wait(client, body["job"])["status"] == "done"
    design = client.get(f"/api/designs/{body['design']['id']}").json()
    assert design["product"] == "coaster"
    result = design["result"]
    assert result["product"] == "coaster"
    assert [p["name"] for p in result["parts"]] == ["plate", "motif"]
    assert {f["role"] for f in result["features"]} == {"motif"}
    for name in ("coaster.stl.zip", "coaster.3mf", "coaster.bambu.3mf", "plate.stl", "motif.stl"):
        res = client.get(f"/api/designs/{design['id']}/files/{name}?download=true")
        assert res.status_code == 200, name
    assert (
        "hi.stl.zip"
        in client.get(f"/api/designs/{design['id']}/files/coaster.stl.zip?download=true").headers[
            "content-disposition"
        ]
    )

    res = client.patch(
        f"/api/designs/{design['id']}",
        json={"coaster": {**design["coaster"], "opener": "coin"}, "roles": {"m2": "ignore"}},
    )
    wait(client, res.json()["job"])
    changed = client.get(f"/api/designs/{design['id']}").json()
    assert changed["result"]["pause_z"] == 3.8
    assert changed["result"]["dimensions"]["width"] > 150

    res = client.patch(f"/api/designs/{design['id']}", json={"product": "cutter"})
    wait(client, res.json()["job"])
    cutter = client.get(f"/api/designs/{design['id']}").json()
    assert cutter["result"]["product"] == "cutter"
    assert client.get(f"/api/designs/{design['id']}/files/cutter.stl").status_code == 200


def test_meta_has_coaster_defaults(client):
    meta = client.get("/api/meta").json()
    assert meta["defaults"]["coaster"]["shape"] == "round"
    assert meta["coins"]["eur2"]["diameter"] == 25.75
    stl = next(f for f in meta["formats"] if f["id"] == "stl")
    assert stl["filenames"] == {"cutter": "cutter.stl", "coaster": "coaster.stl.zip"}


def test_hosting_is_off_locally(client):
    assert client.get("/api/meta").json()["hosting"] is None


def test_hosting_mode(client, monkeypatch):
    from pic2cookie import settings

    monkeypatch.setenv("PIC2COOKIE_HOSTING__ENABLED", "true")
    monkeypatch.setenv("PIC2COOKIE_HOSTING__OPERATOR__NAME", "Jane Doe")
    monkeypatch.setenv("PIC2COOKIE_RETENTION__DAYS", "30")
    settings.settings.cache_clear()
    hosting = client.get("/api/meta").json()["hosting"]
    assert hosting["repository_url"] == "https://github.com/LevinTheDoctor/pic2cookie"
    assert hosting["operator"]["name"] == "Jane Doe"
    assert hosting["retention_days"] == 30
