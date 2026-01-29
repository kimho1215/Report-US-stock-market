import base64
import os

files = [
    'credentials.json',
    'token_youtube.json',
    'token_slides.json',
    'token_email.json'
]

print("=== GitHub Secrets Base64 Strings ===")
print("Copy these values to your GitHub Repository Secrets:\n")

for f in files:
    if os.path.exists(f):
        with open(f, 'rb') as file:
            encoded = base64.b64encode(file.read()).decode('utf-8')
            secret_name = f.replace('.', '_').upper()
            print(f"{secret_name}:")
            print(encoded)
            print("-" * 20)
    else:
        print(f"Warning: {f} not found. Make sure you have authenticated locally first.")
