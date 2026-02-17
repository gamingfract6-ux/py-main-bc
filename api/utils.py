import os, json
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Security constants
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# AI Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Security Helpers ---
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- AI Helpers ---
def get_gemini_vision_model():
    return genai.GenerativeModel('models/gemini-2.5-flash')

def get_gemini_pro_model():
    return genai.GenerativeModel('models/gemini-2.5-flash')

def analyze_food_image(image_data: bytes, content_type: str):
    if not GEMINI_API_KEY:
        return {
            "error": "Gemini API Key not configured",
            "mock_data": True,
            "items": [{"name": "Mock Food", "calories": 250}],
            "calories": 250.0, "protein": 10.0, "carbs": 30.0, "fats": 8.0
        }
    
    model = get_gemini_vision_model()
    prompt = """
    Analyze this food image and provide the nutrition information in a strict JSON format.
    Include: 
    1. 'items': List of objects with:
       - 'name': (string) 
       - 'confidence': (float 0.0 to 1.0)
       - 'calories': (float)
       - 'protein': (float)
       - 'carbs': (float)
       - 'fats': (float)
       - 'fiber': (float)
       - 'sugar': (float)
       - 'sodium': (float)
       - 'portion': (string, e.g., '1 cup', '100g')
       - 'weight_grams': (float)
    2. 'total_calories': sum of calories.
    3. 'total_protein': sum of protein.
    4. 'total_carbs': sum of carbs.
    5. 'total_fats': sum of fats.
    6. 'health_score': (string, 'A', 'B', 'C', or 'D')
    7. 'dietary_tags': (list of strings, e.g., ['Vegetarian', 'High Protein'])
    8. 'ai_insights': (string, brief summary of the meal's healthiness)
    """
    
    response = model.generate_content([
        prompt,
        {"mime_type": content_type, "data": image_data}
    ])
    
    print(f"DEBUG: Gemini Raw Response: {response.text}")
    
    try:
        # Extract JSON from the response text
        text = response.text
        # Clean markdown formatting if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        print(f"DEBUG: Cleaned Text for JSON parsing: {text}")
        data = json.loads(text)
        print(f"DEBUG: Parsed JSON Data: {data}")
        
        return {
            "items": data.get("items", []),
            "calories": float(data.get("total_calories", 0)),
            "protein": float(data.get("total_protein", 0)),
            "carbs": float(data.get("total_carbs", 0)),
            "fats": float(data.get("total_fats", 0)),
            "health_score": data.get("health_score", "B"),
            "dietary_tags": data.get("dietary_tags", []),
            "ai_insights": data.get("ai_insights", "Balanced meal.")
        }
    except Exception as e:
        error_str = str(e)
        print(f"DEBUG: AI Error encountered: {error_str}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"AI Analysis failed: {error_str}",
            "raw_text": getattr(response, 'text', 'No response text available')
        }

def get_ai_coach_response(message: str, user_context: Optional[str] = None):
    if not GEMINI_API_KEY:
        return "I am currently in offline mode. Please configure the Gemini API Key to talk to the AI Coach."
    
    model = get_gemini_pro_model()
    prompt = f"You are a friendly Nutrition Coach for the app 'Find Your Food'. User says: {message}"
    if user_context:
        prompt += f"\nUser Goal: {user_context}"
        
    response = model.generate_content(prompt)
    return response.text

def test_gemini_connection(api_key: Optional[str] = None):
    """Diagnostic function to test if the API key is working"""
    target_key = api_key or GEMINI_API_KEY
    if not target_key:
        return {"success": False, "error": "API Key missing"}
    
    try:
        # Temporarily reconfigure if a specific key is provided
        if api_key:
            genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content("Say 'Connection Successful'")
        
        # Restore original config if we changed it
        if api_key and GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            
        return {"success": True, "response": response.text}
    except Exception as e:
        # Restore original config even on error
        if api_key and GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            
        error_str = str(e)
        status_code = None
        if "429" in error_str or "Quota exceeded" in error_str or "ResourceExhausted" in error_str:
            status_code = 429
        elif "403" in error_str or "permission" in error_str.lower():
            status_code = 403
        elif "401" in error_str or "invalid" in error_str.lower():
            status_code = 401
            
        return {
            "success": False, 
            "error": error_str, 
            "status_code": status_code
        }
