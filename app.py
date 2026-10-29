from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os

from database.poweryoga_db import (
    init_db,
    add_client,
    get_all_clients,
    get_client_by_id,
    update_client,
    delete_client,
    add_progress,
    get_client_progress,
    save_plan,
    get_client_plans,
)
from ai_service import generate_power_yoga_plan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure DB is initialized
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Power Yoga Coach API",
    description="بک‌اند مدیریت شاگردان و دریافت برنامه آنلاین پاور یوگا و رژیم غذایی هوشمند",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for mobile apps and WebViews
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ClientCreate(BaseModel):
    first_name: str = Field(..., description="نام شاگرد")
    last_name: str = Field(..., description="نام خانوادگی")
    age: int = Field(..., gt=0, description="سن شاگرد")
    height: float = Field(..., gt=0, description="قد به سانتی‌متر")
    weight: float = Field(..., gt=0, description="وزن به کیلوگرم")
    training_history: str = Field("", description="سوابق ورزشی و تمرینی")

class ClientUpdate(BaseModel):
    first_name: str
    last_name: str
    age: int
    height: float
    weight: float
    training_history: str

class ProgressCreate(BaseModel):
    weight: float = Field(..., gt=0, description="وزن جدید")
    notes: str = Field("", description="توضیحات و بازخورد")

class PlanGenerateRequest(BaseModel):
    plan_type: str = Field("combined", description="نوع برنامه: workout, diet, or combined")

# Routes
@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Power Yoga API is running"}

@app.post("/api/clients", response_model=Dict[str, Any])
def create_client(client: ClientCreate):
    init_db()
    client_id = add_client(
        first_name=client.first_name,
        last_name=client.last_name,
        age=client.age,
        height=client.height,
        weight=client.weight,
        training_history=client.training_history,
    )
    return {"id": client_id, "message": "شاگرد با موفقیت ثبت شد."}

@app.get("/api/clients", response_model=List[Dict[str, Any]])
def list_clients():
    init_db()
    return get_all_clients()

@app.get("/api/clients/{client_id}", response_model=Dict[str, Any])
def get_client(client_id: int = Path(..., gt=0)):
    init_db()
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="شاگرد یافت نشد.")
    return client

@app.put("/api/clients/{client_id}", response_model=Dict[str, Any])
def edit_client(client: ClientUpdate, client_id: int = Path(..., gt=0)):
    init_db()
    existing = get_client_by_id(client_id)
    if not existing:
        raise HTTPException(status_code=404, detail="شاگرد یافت نشد.")
    update_client(
        client_id=client_id,
        first_name=client.first_name,
        last_name=client.last_name,
        age=client.age,
        height=client.height,
        weight=client.weight,
        training_history=client.training_history,
    )
    return {"message": "اطلاعات شاگرد به‌روزرسانی شد."}

@app.delete("/api/clients/{client_id}", response_model=Dict[str, Any])
def remove_client(client_id: int = Path(..., gt=0)):
    init_db()
    existing = get_client_by_id(client_id)
    if not existing:
        raise HTTPException(status_code=404, detail="شاگرد یافت نشد.")
    delete_client(client_id)
    return {"message": "شاگرد حذف شد."}

@app.post("/api/clients/{client_id}/progress", response_model=Dict[str, Any])
def record_progress(progress: ProgressCreate, client_id: int = Path(..., gt=0)):
    init_db()
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="شاگرد یافت نشد.")
    progress_id = add_progress(client_id=client_id, weight=progress.weight, notes=progress.notes)
    return {"id": progress_id, "message": "سابقه پیشرفت ثبت شد."}

@app.get("/api/clients/{client_id}/progress", response_model=List[Dict[str, Any]])
def list_progress(client_id: int = Path(..., gt=0)):
    init_db()
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="شاگرد یافت نشد.")
    return get_client_progress(client_id)

@app.post("/api/clients/{client_id}/generate-plan", response_model=Dict[str, Any])
def generate_plan_endpoint(req: PlanGenerateRequest, client_id: int = Path(..., gt=0)):
    init_db()
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="شاگرد یافت نشد.")
    progress_logs = get_client_progress(client_id)

    plan_content = generate_power_yoga_plan(client, progress_logs)
    title = f"برنامه آنلاین پاور یوگا و رژیم غذایی - {client['first_name']} {client['last_name']}"

    plan_id = save_plan(client_id=client_id, plan_type=req.plan_type, title=title, content=plan_content)
    return {
        "id": plan_id,
        "title": title,
        "content": plan_content,
        "message": "برنامه هوشمند با موفقیت تولید و ذخیره شد."
    }

@app.get("/api/clients/{client_id}/plans", response_model=List[Dict[str, Any]])
def list_plans(client_id: int = Path(..., gt=0)):
    init_db()
    client = get_client_by_id(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="شاگرد یافت نشد.")
    return get_client_plans(client_id)

# Serve static web frontend for Android WebView / App
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

    @app.get("/")
    def read_index():
        return FileResponse("static/index.html")
