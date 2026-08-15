from detector import scan_code

# Test 1 — AWS Key
def test_aws():
    code = 'key = "AKIAIOSFODNN7EXAMPLE"'
    result = scan_code(code)
    if result["total_found"] > 0:
        print(" AWS Key detected correctly")
    else:
        print(" AWS Key NOT detected — check regex")

# Test 2 — Clean code (no secrets)
def test_clean():
    code = 'name = "Aadesh"\nprint(name)'
    result = scan_code(code)
    if result["total_found"] == 0:
        print(" Clean code passed correctly")
        print(f" Score is {result['score']} / 100")
    else:
        print(" False positive — clean code flagged")

# Test 3 — Multiple secrets
def test_multiple():
    code = '''
password = "secret123"
STRIPE = "stripe_key_placeholder"
DB = "postgresql://admin:pass@localhost/db"
    '''
    result = scan_code(code)
    print(f" Found {result['total_found']} secrets")
    print(f" Score: {result['score']} / 100")

# Run all tests
print("Running tests...\n")
test_aws()
test_clean()
test_multiple()
print("\nDone!")
