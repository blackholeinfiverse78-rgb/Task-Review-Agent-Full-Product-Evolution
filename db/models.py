from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, Float, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Builder(Base):
    __tablename__ = 'builders'
    id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    assignments = relationship("AssignmentModel", back_populates="builder")

class Product(Base):
    __tablename__ = 'products'
    id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    repositories = relationship("Repository", back_populates="product")
    certifications = relationship("CertificationModel", back_populates="product")
    historical_metrics = relationship("HistoricalMetricModel", back_populates="product")
    participations = relationship("ProductParticipationModel", back_populates="product")

class Repository(Base):
    __tablename__ = 'repositories'
    id = Column(String(100), primary_key=True)
    product_id = Column(String(100), ForeignKey('products.id'), nullable=False)
    repo_url = Column(String(255), nullable=False)
    branch = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    product = relationship("Product", back_populates="repositories")

class TaskSubmissionModel(Base):
    __tablename__ = 'task_submissions'
    submission_id = Column(String(100), primary_key=True)
    task_id = Column(String(100), index=True, nullable=False)
    task_title = Column(String(255), nullable=False)
    task_description = Column(Text, nullable=False)
    submitted_by = Column(String(100), nullable=False)
    submitted_at = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)
    previous_task_id = Column(String(100), nullable=True)
    pdf_file_path = Column(String(500), nullable=True)
    pdf_extracted_text = Column(Text, nullable=True)
    module_id = Column(String(100), nullable=True)
    schema_version = Column(String(20), nullable=True)
    registry_validation_status = Column(String(50), nullable=True)
    registry_validation_reason = Column(Text, nullable=True)
    review_state = Column(String(50), nullable=True)
    deleted_at = Column(DateTime, nullable=True)

class ReviewModel(Base):
    __tablename__ = 'reviews'
    review_id = Column(String(100), primary_key=True)
    submission_id = Column(String(100), index=True, nullable=False)
    trace_id = Column(String(100), nullable=True)
    evaluation_result = Column(String(20), nullable=False)  # "PASS" | "FAIL"
    score = Column(Integer, nullable=False)
    readiness_percent = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # "pass" | "fail" | "borderline"
    decision = Column(String(20), nullable=False)  # "APPROVED" | "REJECTED"
    reviewed_by = Column(String(100), nullable=False)
    reviewed_at = Column(DateTime, nullable=False)
    evaluation_time_ms = Column(Integer, default=0)
    evaluation_summary = Column(Text, nullable=True)
    review_state = Column(String(50), default="PENDING_REVIEW")
    version = Column(Integer, default=1)
    candidate_name = Column(String(100), nullable=True)
    task_title = Column(String(255), nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    evidences = relationship("EvidenceModel", back_populates="review")
    artifacts = relationship("ArtifactModel", back_populates="review")
    dimension_results = relationship("DimensionResultModel", back_populates="review")
    assignments = relationship("AssignmentModel", back_populates="review")
    risks = relationship("RiskRegisterModel", back_populates="review")

class EvidenceModel(Base):
    __tablename__ = 'evidence'
    id = Column(String(100), primary_key=True)
    review_id = Column(String(100), ForeignKey('reviews.review_id'), nullable=False)
    type = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=True)
    extracted_text = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    review = relationship("ReviewModel", back_populates="evidences")

class ArtifactModel(Base):
    __tablename__ = 'artifacts'
    id = Column(String(100), primary_key=True)
    review_id = Column(String(100), ForeignKey('reviews.review_id'), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=True)
    checksum = Column(String(100), nullable=True)
    version_metadata = Column(Text, nullable=True)  # JSON representation
    created_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("ReviewModel", back_populates="artifacts")

class TraceSessionModel(Base):
    __tablename__ = 'trace_sessions'
    id = Column(String(100), primary_key=True)
    trace_id = Column(String(100), unique=True, index=True, nullable=False)
    review_id = Column(String(100), ForeignKey('reviews.review_id'), nullable=True)
    system_status = Column(String(50), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    log_file_path = Column(String(500), nullable=True)

class ReplayRecordModel(Base):
    __tablename__ = 'replay_records'
    id = Column(String(100), primary_key=True)
    trace_id = Column(String(100), nullable=False)
    original_review_id = Column(String(100), nullable=False)
    replay_review_id = Column(String(100), nullable=False)
    is_deterministic = Column(Boolean, nullable=False)
    discrepancies = Column(Text, nullable=True)  # JSON representation
    replayed_at = Column(DateTime, default=datetime.utcnow)

class CertificationModel(Base):
    __tablename__ = 'certifications'
    id = Column(String(100), primary_key=True)
    trace_id = Column(String(100), nullable=False)
    product_id = Column(String(100), ForeignKey('products.id'), nullable=False)
    certification_type = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False)
    score = Column(Integer, nullable=False)
    certified_at = Column(DateTime, default=datetime.utcnow)
    expiry_at = Column(DateTime, nullable=True)
    certificate_path = Column(String(500), nullable=True)

    product = relationship("Product", back_populates="certifications")

class AssignmentModel(Base):
    __tablename__ = 'assignments'
    id = Column(String(100), primary_key=True)
    builder_id = Column(String(100), ForeignKey('builders.id'), nullable=True)
    review_id = Column(String(100), ForeignKey('reviews.review_id'), nullable=True)
    previous_submission_id = Column(String(100), nullable=True)
    next_task_id = Column(String(100), nullable=False)

    task_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    objective = Column(Text, nullable=False)
    focus_area = Column(String(100), nullable=False)
    difficulty = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    priority = Column(String(20), default="Medium")
    category = Column(String(100), nullable=True)
    est_ai_effort = Column(String(50), nullable=True)
    learning_resources = Column(Text, nullable=True)  # JSON list
    review_checklist = Column(Text, nullable=True)  # JSON list
    status = Column(String(50), default="assigned")
    assigned_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    builder = relationship("Builder", back_populates="assignments")
    review = relationship("ReviewModel", back_populates="assignments")

class DecisionLedgerModel(Base):
    __tablename__ = 'decision_ledger'
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    actor = Column(String(100), nullable=False)
    reason = Column(Text, nullable=True)
    original_state = Column(Text, nullable=True)
    new_state = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RiskRegisterModel(Base):
    __tablename__ = 'risk_register'
    id = Column(String(100), primary_key=True)
    review_id = Column(String(100), ForeignKey('reviews.review_id'), nullable=False)
    risk_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    mitigation = Column(Text, nullable=True)
    status = Column(String(50), default="identified")
    identified_at = Column(DateTime, default=datetime.utcnow)

    review = relationship("ReviewModel", back_populates="risks")

class HistoricalMetricModel(Base):
    __tablename__ = 'historical_metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_date = Column(DateTime, default=datetime.utcnow)
    product_id = Column(String(100), ForeignKey('products.id'), nullable=False)
    readiness_score = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    total_reviews = Column(Integer, default=0)
    passed_reviews = Column(Integer, default=0)
    failed_reviews = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="historical_metrics")

class GovernanceRecordModel(Base):
    __tablename__ = 'governance_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(100), nullable=False)
    event_id = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    actor = Column(String(100), nullable=False)
    signature = Column(String(255), nullable=True)
    parent_hash = Column(String(100), nullable=True)
    current_hash = Column(String(100), nullable=True)
    payload = Column(Text, nullable=True)  # JSON representation
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductParticipationModel(Base):
    __tablename__ = 'product_participation'
    id = Column(String(100), primary_key=True)
    product_id = Column(String(100), ForeignKey('products.id'), nullable=False)
    role = Column(String(100), nullable=False)
    status = Column(String(50), default="active")
    integration_scope = Column(Text, nullable=True)  # JSON representation
    registered_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="participations")

class DimensionResultModel(Base):
    __tablename__ = 'dimension_results'
    id = Column(String(100), primary_key=True)
    review_id = Column(String(100), ForeignKey('reviews.review_id'), nullable=False)
    dimension_name = Column(String(100), nullable=False)
    score = Column(Float, nullable=False)
    detail = Column(Text, nullable=True)
    passed = Column(Boolean, nullable=False)

    review = relationship("ReviewModel", back_populates="dimension_results")

class AuditLogModel(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    trace_id = Column(String(100), nullable=True)
    event_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    actor = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action_taken = Column(Text, nullable=False)
    details = Column(Text, nullable=True)


class SpentTokenModel(Base):
    __tablename__ = 'spent_tokens'
    token_hash = Column(String(64), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

