import _winapi
import inspect

print("Attributes of _winapi:")
for attr in dir(_winapi):
    if "CreateProcess" in attr:
        print(f"- {attr}")

try:
    print(f"\nSignature of CreateProcess: {inspect.signature(_winapi.CreateProcess)}")
except ValueError:
    print("\nCould not get signature via inspect (likely a C function).")
