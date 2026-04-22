# test_api.py — Test before submitting
import requests, json

BASE_URL = "http://localhost:8000"

def test(name, payload):
    print(f"\n{'='*55}")
    print(f"TEST: {name}")
    print(f"INPUT: {json.dumps(payload)}")
    try:
        resp = requests.post(f"{BASE_URL}/v1/answer", json=payload, timeout=30)
        data = resp.json()
        print(f"STATUS: {resp.status_code}")
        print(f"OUTPUT: {data.get('output', data)}")
        ok = resp.status_code == 200 and "output" in data
        print("✅ PASS" if ok else "❌ FAIL")
    except Exception as e:
        print(f"❌ ERROR: {e}")

# Level 1 public test case
test("Level 1 — What is 10 + 15?", {"query": "What is 10 + 15?", "assets": []})
test("Math — What is 100 divided by 4?", {"query": "What is 100 divided by 4?", "assets": []})
test("With URL asset", {"query": "What is artificial intelligence?", "assets": ["https://en.wikipedia.org/wiki/Artificial_intelligence"]})

print(f"\n{'='*55}")
print("Done! Check outputs above.")
