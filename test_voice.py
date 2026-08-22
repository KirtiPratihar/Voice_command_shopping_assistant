from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

def run_test(cmd, pref):
    payload = {"text": cmd, "user_id": "test-user", "preference": pref}
    r = client.post('/voice-command', json=payload)
    print(f"\n=== Preference: {pref} | Command: {cmd} | Status: {r.status_code} ===")
    try:
        print(r.json())
    except Exception as e:
        print('Failed to decode JSON:', e)

# Run several samples
run_test('Add one bread to my cart', 'budget')
run_test('Add one bread to my cart', 'premium')
run_test('Add two milk cartons', 'budget')
run_test('Add two milk cartons', 'premium')
