# -*- coding: utf-8 -*-
"""Vérifie que le backend sert la SPA buildée + injecte <base href> pour l'ingress."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["MP_DB_PATH"] = os.path.join(_root, "backend", "tests", "serve.db")
os.environ["MP_FRONTEND_DIST"] = os.path.join(_root, "frontend", "dist")
for ext in ("", "-wal", "-shm"):
    p = os.environ["MP_DB_PATH"] + ext
    if os.path.exists(p):
        os.remove(p)

from fastapi.testclient import TestClient
import backend.main as m

with TestClient(m.app) as client:
    # Racine avec header ingress -> <base href> injecté
    r = client.get("/", headers={"X-Ingress-Path": "/api/hassio_ingress/abc123"})
    assert r.status_code == 200, r.status_code
    assert '<base href="/api/hassio_ingress/abc123/">' in r.text, "base href non injecté"
    assert 'id="root"' in r.text or "root" in r.text
    print("Racine servie + <base href> ingress injecté : OK")

    # Sans header -> base relatif './'
    r2 = client.get("/")
    assert '<base href="./">' in r2.text
    print("Racine sans ingress -> base './' : OK")

    # Manifest + service worker servis en statique
    assert client.get("/manifest.json").status_code == 200
    assert client.get("/sw.json" if False else "/sw.js").status_code == 200
    print("manifest.json + sw.js servis : OK")

    # Route SPA inconnue -> fallback index (client-side routing)
    r3 = client.get("/planning")
    assert r3.status_code == 200 and "root" in r3.text
    print("Fallback SPA (route cliente) : OK")

    # API toujours accessible
    assert client.get("/api/health").json()["status"] == "ok"
    print("API /api/health : OK")

for ext in ("", "-wal", "-shm"):
    p = os.environ["MP_DB_PATH"] + ext
    if os.path.exists(p):
        os.remove(p)
print("\nSERVE CHECK OK")
