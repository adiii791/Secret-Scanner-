
# Secret Checker - Version 2


def check_for_secret(code, secret_word):
 # this function checks if secrets word in present in this function.
    if secret_word in code.lower():
        return True
    return False

def scan_all_secrets(code):
 # this function scan all type of secrets from this function.
    secrets_list = ["password", "api key", "secret", "tokens", "secret", "private key", "aws access"]
    found = []

    for secret in secrets_list:
        if check_for_secret(code, secret):
            found.append(secret)
           
    return found

def print_results(secrets_found):
 # this function is used to print the results perfectly of the scan.
    print()
    print("=" * 50)

    if len(secrets_found) == 0:
        print("✅Your scan is successfully completed and no secrets are found in your code !")
        print("✅Your code is safe to proceed further !")
    else:
        print(f" Total secrets found: {len(secrets_found)}")
        print()
        
        for secret in secrets_found:
            print(f" - {secret} founded !")
        print()
        print("❌Please remove the secrets from your code before commiting it further for the next processes.")

    print("=" * 50)

def main():
 # this function contains the intializing phase of the product and its heading display in the header of the terminal output.    
    print("╔════════════════════════════════════════╗")
    print("║    SECRET CHECKER v2.0                 ║")
    print("║    Your Code Security Assistant        ║")
    print("╚════════════════════════════════════════╝")
    print()

    code = input("Enter or Paste your code here:\n")

    print()
    print("🔍Scanning...")

    results = scan_all_secrets(code)
    print_results(results)

    print()
    print(f"Lines scanned : 1")
    print(f"Secrets found : {len(results)} ")
    print(f"Safety Score for your code is : {100 - (len(results) * 20)}%")

if __name__ == "__main__":
    main()


# # Secret Checker - Version 1 


# print("=== Secret Checker ===")
# print("Enter your code:")
# print()

# code = input("Code: ")

# secrets_found = 0

# if "password" in code.lower():
#     print("⚠️  Found: password")
#     secrets_found = secrets_found + 1

# if "api_key" in code.lower():
#     print("⚠️  Found: api_key")
#     secrets_found = secrets_found + 1

# if "secret" in code.lower():
#     print("⚠️  Found: secret")
#     secrets_found = secrets_found + 1

# if "token" in code.lower():
#     print("⚠️  Found: token")
#     secrets_found = secrets_found + 1

# print()
# print(f"Total secrets found: {secrets_found}")

# if secrets_found == 0:
#     print("✅ Your code is safe!")
# else:
#     print("❌ Remove secrets from your code!")\


# # Secret Checker - Version 3


