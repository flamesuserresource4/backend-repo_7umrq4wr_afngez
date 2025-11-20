import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for globally shared background image)
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# ------------------------------
# Global Finale Background Image
# ------------------------------
FINAL_BG_FILENAME = "finale-bg"
FINAL_BG_ALLOWED_EXT = {"jpg", "jpeg", "png", "webp"}

@app.get("/config/finale-bg")
async def get_finale_bg():
    """Return the shared finale background image URL if present"""
    # Check possible files with allowed extensions
    for ext in ["jpg", "jpeg", "png", "webp"]:
        candidate = os.path.join(STATIC_DIR, f"{FINAL_BG_FILENAME}.{ext}")
        if os.path.exists(candidate):
            return {"url": f"/static/{FINAL_BG_FILENAME}.{ext}"}
    return {"url": None}

@app.post("/config/finale-bg")
async def upload_finale_bg(file: UploadFile = File(...)):
    """Upload and set the shared finale background image (overwrites previous)."""
    # Validate extension
    ext = (file.filename.split(".")[-1] or '').lower()
    if ext not in FINAL_BG_ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(sorted(FINAL_BG_ALLOWED_EXT))}")

    # Remove any existing variants
    for e in list(FINAL_BG_ALLOWED_EXT):
        existing = os.path.join(STATIC_DIR, f"{FINAL_BG_FILENAME}.{e}")
        if os.path.exists(existing):
            try:
                os.remove(existing)
            except Exception:
                pass

    # Save new file
    target_path = os.path.join(STATIC_DIR, f"{FINAL_BG_FILENAME}.{ext}")
    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    return JSONResponse({"url": f"/static/{FINAL_BG_FILENAME}.{ext}"})


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
