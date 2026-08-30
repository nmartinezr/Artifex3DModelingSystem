from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from artifex_api.assets import router as assets_router
from artifex_api.export_routes import router as export_router
from artifex_api.image_to_3d.generation_routes import router as generation_router
from artifex_api.image_to_3d.routes import router as image_to_3d_router

app = FastAPI(title="ARTIFEX API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(assets_router)
app.include_router(image_to_3d_router)
app.include_router(generation_router)
app.include_router(export_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
