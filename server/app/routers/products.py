from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.schemas import ProductResponse

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/{product_code}", response_model=ProductResponse)
def get_product(product_code: str, db: Session = Depends(get_db)):
    p = db.query(models.Product).filter(models.Product.code == product_code).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse(code=p.code, name=p.name, is_paid=p.is_paid)
