from __future__ import annotations
from fastapi import FastAPI
from app.db.database import engine
from app.db.database import Base
from app.db import models
from sqlalchemy.orm import Session
from app.core.config import settings
from app.routers import auth, license, session, products

def create_app() -> FastAPI:
    app = FastAPI(title="HW Lock Licensing Server", version="1.0.0")

    # DB init
    Base.metadata.create_all(bind=engine)

    # seed products if missing
    with Session(engine) as db:
        if db.query(models.Product).count() == 0:
            db.add_all([
                models.Product(code="demo_free", name="Demo Free App", is_paid=False),
                models.Product(code="demo_paid", name="Demo Paid App", is_paid=True),
            ])
            db.commit()

    app.include_router(auth.router)
    app.include_router(products.router)
    app.include_router(license.router)
    app.include_router(session.router)

    @app.get("/health")
    def health():
        return {"ok": True}

    return app

app = create_app()
