#!/usr/bin/env python3
import json
import urllib.request

with open('test_payload.json') as f:
    data = json.load(f)

print(f"📤 Enviando {len(data['scheduling_request']['employees'])} empleados...")

req = urllib.request.Request(
    'http://localhost:5000/api/schedule/generate',
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read())
    print(f"✅ Éxito: {result.get('success')}")
    print(f"📃 Excel: {result.get('file_name')}")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8')  
    print(f"❌ Error {e.code}: {e.reason}")
    if body:
        err = json.loads(body)
        print(f"Detalle: {err.get('message')}")
