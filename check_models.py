import google.generativeai as genai

# PASTE YOUR KEY HERE
MY_KEY = "AIzaSyAfGw2eXQzIvShLCdXDIhpPDtBq1GDRhxk"
genai.configure(api_key=MY_KEY)

print("🔍 Checking available models for your key...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ FOUND: {m.name}")
except Exception as e:
    print(f"❌ Error: {e}")