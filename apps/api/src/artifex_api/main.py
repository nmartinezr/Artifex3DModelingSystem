from fastapi import FastAPI

from artifex_api.image_to_3d.routes import router as image_to_3d_router

app = FastAPI(title="ARTIFEX API", version="0.1.0")
app.include_router(image_to_3d_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
