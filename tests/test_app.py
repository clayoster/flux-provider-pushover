import base64
import os
import subprocess
import json

def test_env_vars():
    assert os.environ["PUSHOVER_USER_KEY"] == "test_user_key"
    assert os.environ["PUSHOVER_API_TOKEN"] == "test_api_token"

def test_good_auth_and_payload(app, client):
    payload = {
        "involvedObject": {
            "kind": "Kustomization",
            "namespace": "flux-system",
            "name": "secrets",
            "uid": "beda5644-ddbe-4b13-a3a9-ce223fb33cf",
            "apiVersion": "kustomize.toolkit.fluxcd.io/v1",
            "resourceVersion": "50060406"
        },
        "severity": "info",
        "timestamp": "2025-09-06T16:47:10Z",
        "message": "Reconciliation finished in 154.143224ms, next run in 10m0s",
        "reason": "ReconciliationSucceeded",
        "metadata": {
            "commit_status": "update",
            "revision": "main@sha1:d11dc3159634606cafccb94cb9c2a22d3fbe90e7",
        },
        "reportingController": "kustomize-controller",
        "reportingInstance": "kustomize-controller-7bcf986f97-mn7gg"
    }

    res = client.post(
        "/webhook",
        headers={"Authorization": "Bearer test_api_token"},
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert res.status_code == 200
    assert b'ok' in res.data

def test_bad_auth(app, client):
    payload = {
        "test": "test"
    }

    res = client.post(
        "/webhook",
        headers={"Authorization": "Bearer bad_token"},
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert res.status_code == 401
    assert b'Unauthorized' in res.data

def test_healthcheck(app, client):
    res = client.get('/health')
    assert b'healthy' in res.data
    assert res.status_code == 200

def test_bareurl(app, client):
    res = client.get('/')
    assert b'Requests need to be made to /webhook' in res.data
    assert res.status_code == 400

def test_without_auth_variables(monkeypatch):
    monkeypatch.delenv("PUSHOVER_USER_KEY", raising=False)
    monkeypatch.delenv("PUSHOVER_API_TOKEN", raising=False)

    result = subprocess.run(["python3", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )

    # Confirm the application fails to start without PUSHOVER_USER_KEY and PUSHOVER_API_TOKEN set
    assert result.returncode != 0
    assert b'Pushover user key or API token is not not configured' in result.stdout
