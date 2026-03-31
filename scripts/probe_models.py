import vertexai
from vertexai.generative_models import GenerativeModel
import google.auth

def list_available_models():
    project_id = "genai-apac-2026-491004"
    region = "us-central1"
    
    vertexai.init(project=project_id, location=region)
    
    # We try common known ones and check their existence via a trivial call
    models_to_check = [
        "gemini-1.5-flash-002",
        "gemini-1.5-flash-001",
        "gemini-1.5-pro-002",
        "gemini-1.5-pro-001",
        "gemini-2.0-flash-001"
    ]
    
    print(f"=== Probing Vertex AI Models in {region} ===")
    for model_name in models_to_check:
        try:
            model = GenerativeModel(model_name)
            # Trivial prompt to check for 404
            response = model.generate_content("hello", generation_config={"max_output_tokens": 1})
            print(f"✅ {model_name}: AVAILABLE")
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print(f"❌ {model_name}: NOT FOUND")
            else:
                print(f"⚠️ {model_name}: ERROR - {e}")

if __name__ == "__main__":
    list_available_models()
