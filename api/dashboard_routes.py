from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from typing import List, Dict, Any

from db.db_config import get_db_session
from db.models import Builder, Product, ReviewModel, CertificationModel, AssignmentModel, RiskRegisterModel, DimensionResultModel

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/builder-quality")
def get_builder_quality(db: Session = Depends(get_db_session)):
    """Retrieve quality metrics aggregated per builder/candidate."""
    try:
        results = db.query(
            ReviewModel.candidate_name,
            func.count(ReviewModel.review_id).label("total_reviews"),
            func.avg(ReviewModel.score).label("average_score"),
            func.sum(case((ReviewModel.evaluation_result == 'PASS', 1), else_=0)).label("passed_reviews")
        ).group_by(ReviewModel.candidate_name).all()

        builders_data = []
        for r in results:
            name = r.candidate_name or "Unknown Builder"
            total = r.total_reviews or 0
            passed = r.passed_reviews or 0
            avg_score = round(float(r.average_score), 2) if r.average_score else 0.0
            pass_rate = round((passed / total) * 100, 2) if total > 0 else 0.0

            builders_data.append({
                "builder_name": name,
                "total_reviews": total,
                "passed_reviews": passed,
                "failed_reviews": total - passed,
                "average_score": avg_score,
                "pass_rate_percent": pass_rate
            })

        return {
            "builders": builders_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch builder quality: {str(e)}")

@router.get("/product-readiness")
def get_product_readiness(db: Session = Depends(get_db_session)):
    """Retrieve certification readiness per ecosystem product."""
    try:
        products = db.query(Product).all()
        products_data = []
        
        for p in products:
            latest_cert = db.query(CertificationModel).filter(
                CertificationModel.product_id == p.id
            ).order_by(CertificationModel.certified_at.desc()).first()

            status = "NOT CERTIFIED"
            score = 0
            certified_at = None
            if latest_cert:
                status = latest_cert.status
                score = latest_cert.score
                certified_at = latest_cert.certified_at.isoformat()

            products_data.append({
                "product_id": p.id,
                "product_name": p.name,
                "certification_status": status,
                "readiness_score": score,
                "certified_at": certified_at
            })

        return {
            "products": products_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch product readiness: {str(e)}")

@router.get("/certification-history")
def get_certification_history(db: Session = Depends(get_db_session)):
    """Retrieve chronological list of past certifications."""
    try:
        certs = db.query(
            CertificationModel.id,
            CertificationModel.trace_id,
            Product.name.label("product_name"),
            CertificationModel.certification_type,
            CertificationModel.status,
            CertificationModel.score,
            CertificationModel.certified_at
        ).join(Product, CertificationModel.product_id == Product.id).order_by(
            CertificationModel.certified_at.desc()
        ).all()

        history = [{
            "id": c.id,
            "trace_id": c.trace_id,
            "product_name": c.product_name,
            "certification_type": c.certification_type,
            "status": c.status,
            "score": c.score,
            "certified_at": c.certified_at.isoformat()
        } for c in certs]

        return {
            "history": history,
            "total_certifications": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch certification history: {str(e)}")

@router.get("/production-scores")
def get_production_scores(db: Session = Depends(get_db_session)):
    """Retrieve average scores and status ratios across all reviews."""
    try:
        reviews = db.query(ReviewModel).all()
        if not reviews:
            return {"average_score": 0.0, "status_distribution": {}, "total_count": 0}

        total_score = sum(r.score for r in reviews)
        avg_score = round(total_score / len(reviews), 2)

        dist = {}
        for r in reviews:
            dist[r.status] = dist.get(r.status, 0) + 1

        return {
            "average_score": avg_score,
            "status_distribution": dist,
            "total_count": len(reviews),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch production scores: {str(e)}")

@router.get("/engineering-trends")
def get_engineering_trends(days: int = 30, db: Session = Depends(get_db_session)):
    """Retrieve review counts aggregated daily over a specified window."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        results = db.query(
            func.date(ReviewModel.reviewed_at).label("day"),
            func.count(ReviewModel.review_id).label("count"),
            func.avg(ReviewModel.score).label("avg_score")
        ).filter(ReviewModel.reviewed_at >= cutoff).group_by(func.date(ReviewModel.reviewed_at)).order_by("day").all()

        trends = [{
            "date": str(r.day),
            "reviews_count": r.count,
            "average_score": round(float(r.avg_score), 2) if r.avg_score else 0.0
        } for r in results]

        return {
            "window_days": days,
            "trends": trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch engineering trends: {str(e)}")

@router.get("/open-reviews")
def get_open_reviews(db: Session = Depends(get_db_session)):
    """Retrieve all reviews waiting in the manual escalation queue."""
    try:
        reviews = db.query(ReviewModel).filter(
            ReviewModel.review_state == "PENDING_REVIEW",
            ReviewModel.deleted_at.is_(None)
        ).all()

        return {
            "pending_count": len(reviews),
            "reviews": [{
                "review_id": r.review_id,
                "submission_id": r.submission_id,
                "trace_id": r.trace_id,
                "score": r.score,
                "reviewed_at": r.reviewed_at.isoformat(),
                "candidate_name": r.candidate_name,
                "task_title": r.task_title
            } for r in reviews]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch open reviews: {str(e)}")

@router.get("/risk-register")
def get_risk_register(db: Session = Depends(get_db_session)):
    """Retrieve all identified risks from task reviews."""
    try:
        risks = db.query(RiskRegisterModel).filter(RiskRegisterModel.status != "mitigated").all()
        return {
            "active_risks_count": len(risks),
            "risks": [{
                "id": r.id,
                "review_id": r.review_id,
                "risk_type": r.risk_type,
                "severity": r.severity,
                "description": r.description,
                "mitigation": r.mitigation,
                "status": r.status,
                "identified_at": r.identified_at.isoformat()
            } for r in risks]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch risk register: {str(e)}")

@router.get("/governance-issues")
def get_governance_issues(db: Session = Depends(get_db_session)):
    """Retrieve all critical failures and unapproved releases."""
    try:
        failures = db.query(ReviewModel).filter(
            ReviewModel.evaluation_result == "FAIL",
            ReviewModel.deleted_at.is_(None)
        ).order_by(ReviewModel.reviewed_at.desc()).all()

        return {
            "unapproved_releases_count": len(failures),
            "issues": [{
                "review_id": f.review_id,
                "trace_id": f.trace_id,
                "decision": f.decision,
                "score": f.score,
                "reviewed_at": f.reviewed_at.isoformat(),
                "failure_reasons": f.failure_reasons
            } for f in failures]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch governance issues: {str(e)}")

@router.get("/assignment-queue")
def get_assignment_queue(db: Session = Depends(get_db_session)):
    """Retrieve active next tasks grouped by priority."""
    try:
        assignments = db.query(AssignmentModel).filter(
            AssignmentModel.status == "assigned",
            AssignmentModel.deleted_at.is_(None)
        ).all()

        queued = []
        for a in assignments:
            queued.append({
                "assignment_id": a.id,
                "next_task_id": a.next_task_id,
                "title": a.title,
                "difficulty": a.difficulty,
                "priority": a.priority,
                "category": a.category,
                "est_ai_effort": a.est_ai_effort,
                "assigned_at": a.assigned_at.isoformat(),
                "builder_id": a.builder_id
            })

        # Group by priority
        by_priority = {"Critical": [], "High": [], "Medium": [], "Low": []}
        for item in queued:
            priority = item["priority"]
            if priority in by_priority:
                by_priority[priority].append(item)
            else:
                by_priority["Medium"].append(item)

        return {
            "total_assigned": len(queued),
            "by_priority": by_priority
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch assignment queue: {str(e)}")

@router.get("/ecosystem-health")
def get_ecosystem_health(db: Session = Depends(get_db_session)):
    """Retrieve high-level combined ecosystem KPIs."""
    try:
        total_products = db.query(Product).count()
        
        # Calculate certified count
        all_certs = db.query(CertificationModel).all()
        latest_certs = {}
        for c in all_certs:
            if c.product_id not in latest_certs or c.certified_at > latest_certs[c.product_id].certified_at:
                latest_certs[c.product_id] = c
        certified_products = sum(1 for c in latest_certs.values() if c.status in ("READY", "READY WITH OBSERVATIONS"))

        total_reviews = db.query(ReviewModel).count()
        total_passed = db.query(ReviewModel).filter(ReviewModel.evaluation_result == "PASS").count()
        compliance_pct = round((total_passed / total_reviews) * 100, 2) if total_reviews > 0 else 100.0

        active_assignments = db.query(AssignmentModel).filter(
            AssignmentModel.status == "assigned",
            AssignmentModel.deleted_at.is_(None)
        ).count()

        active_risks = db.query(RiskRegisterModel).filter(RiskRegisterModel.status != "mitigated").count()

        health_status = "HEALTHY"
        if compliance_pct < 70 or active_risks > 10:
            health_status = "DEGRADED"
        if compliance_pct < 50 or active_risks > 20:
            health_status = "CRITICAL"

        return {
            "status": health_status,
            "total_products": total_products,
            "certified_products": certified_products,
            "certification_ratio": round((certified_products / total_products) * 100, 2) if total_products > 0 else 0.0,
            "compliance_ratio_percent": compliance_pct,
            "active_tasks_count": active_assignments,
            "unresolved_risks_count": active_risks,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ecosystem health: {str(e)}")
