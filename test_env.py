import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test API key loading
api_key = os.getenv("GEMINI_API_KEY")

print("=== Environment Variable Test ===")
print(f"API Key loaded: {api_key}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"API Key starts with 'AIza': {api_key.startswith('AIza') if api_key else False}")
print(f"Is API Key valid format: {api_key != 'YOUR_API_KEY_HERE' if api_key else False}")

# Check if .env file exists
if os.path.exists('.env'):
    print("✅ .env file exists")
    with open('.env', 'r') as f:
        content = f.read()
        print(f"✅ .env file content length: {len(content)} characters")
        if 'GEMINI_API_KEY' in content:
            print("✅ GEMINI_API_KEY found in .env file")
        else:
            print("❌ GEMINI_API_KEY not found in .env file")
else:
    print("❌ .env file not found")

# Test Gemini API connection
try:
    import google.generativeai as genai
    if api_key and api_key != "YOUR_API_KEY_HERE":
        genai.configure(api_key=api_key)
        print("✅ Gemini API configured successfully")
        
        # Test with a simple model call
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Model created successfully")
    else:
        print("❌ Invalid API key")
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}")