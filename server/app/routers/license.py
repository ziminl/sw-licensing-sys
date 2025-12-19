from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models
from app.core.schemas import RedeemRequest, RedeemResponse, LicenseValidateRequest, LicenseValidateResponse
from app.core.deps import get_current_user, get_current_session
from app.core.license_codec import decode_and_verify, payload_exp_datetime
from app.core.security import utcnow

router = APIRouter(prefix="/license", tags=["license"])

def _get_product_or_404(db: Session, code: str) -> models.Product:
    p = db.query(models.Product).filter(models.Product.code == code).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p

@router.post("/redeem", response_model=RedeemResponse)
def redeem(
    req: RedeemRequest,
    user: models.User = Depends(get_current_user),
    sess: models.Session = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    p = _get_product_or_404(db, req.product_code)
    if not p.is_paid:
        raise HTTPException(status_code=400, detail="Product is free. No license needed.")

    # HWID는 세션의 HWID와 일치해야 함
    if req.hwid_hash != sess.hwid_hash:
        raise HTTPException(status_code=400, detail="HWID mismatch with current session")

    payload, err = decode_and_verify(req.license_code)
    if err:
        raise HTTPException(status_code=400, detail=f"License invalid: {err}")
    if payload["product"] != p.code:
        raise HTTPException(status_code=400, detail="License not for this product")

    exp_dt = payload_exp_datetime(payload)

    # DB에 있는지 확인
    lc = db.query(models.LicenseCode).filter(models.LicenseCode.code == req.license_code).first()
    if lc is None:
        lc = models.LicenseCode(
            code=req.license_code,
            product_id=p.id,
            expires_at=exp_dt,
            redeemed_by_user_id=None,
            redeemed_at=None,
            bound_hwid_hash=None,
            is_revoked=False,
        )
        db.add(lc)
        db.commit()
        db.refresh(lc)

    if lc.is_revoked:
        raise HTTPException(status_code=403, detail=f"License revoked: {lc.revoke_reason or 'REVOKED'}")

    # 이미 redeem 되었는지
    if lc.redeemed_by_user_id is not None and lc.redeemed_by_user_id != user.id:
        raise HTTPException(status_code=409, detail="License already redeemed by another account")

    # bind HWID (최초 1회)
    if lc.bound_hwid_hash is None:
        lc.bound_hwid_hash = req.hwid_hash
    elif lc.bound_hwid_hash != req.hwid_hash:
        # HWID 변경 시 무효 처리(재인증 요구)
        raise HTTPException(status_code=403, detail="HWID changed. Re-activation required.")

    lc.redeemed_by_user_id = user.id
    lc.redeemed_at = utcnow()
    db.commit()
    db.refresh(lc)

    return RedeemResponse(ok=True, product_code=p.code, expires_at=lc.expires_at, bound_hwid_hash=lc.bound_hwid_hash)

@router.post("/validate", response_model=LicenseValidateResponse)
def validate(
    req: LicenseValidateRequest,
    user: models.User = Depends(get_current_user),
    sess: models.Session = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    p = _get_product_or_404(db, req.product_code)

    # Free 제품은 로그인만으로 valid
    if not p.is_paid:
        return LicenseValidateResponse(valid=True, product_code=p.code)

    # Paid 제품: redeem된 라이선스가 있어야 함 (1개 이상)
    lcs = (
        db.query(models.LicenseCode)
          .filter(models.LicenseCode.product_id == p.id, models.LicenseCode.redeemed_by_user_id == user.id)
          .all()
    )
    if not lcs:
        return LicenseValidateResponse(valid=False, product_code=p.code, reason="NO_LICENSE")

    # 세션 HWID와 요청 HWID 일치
    if req.hwid_hash != sess.hwid_hash:
        return LicenseValidateResponse(valid=False, product_code=p.code, reason="HWID_MISMATCH_SESSION")

    # 어떤 라이선스든 유효하면 OK (가장 좋은 것 선택)
    now = utcnow()
    for lc in lcs:
        if lc.is_revoked:
            continue
        if lc.bound_hwid_hash and lc.bound_hwid_hash != req.hwid_hash:
            continue
        if lc.expires_at and now > lc.expires_at:
            continue
        return LicenseValidateResponse(valid=True, product_code=p.code, expires_at=lc.expires_at)

    return LicenseValidateResponse(valid=False, product_code=p.code, reason="NO_VALID_LICENSE")
