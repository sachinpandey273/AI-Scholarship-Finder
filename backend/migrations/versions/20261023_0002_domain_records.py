"""Add document, source, evidence, decision, draft, and audit records.

Revision ID: 20261023_0002
Revises: 20261023_0001
"""
from alembic import op
import sqlalchemy as sa
revision = "20261023_0002"
down_revision = "20261023_0001"
branch_labels = None
depends_on = None

def table(name, *columns): op.create_table(name, *columns, sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
def upgrade():
    table("uploaded_documents", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("storage_key", sa.String(512), unique=True, nullable=False), sa.Column("original_filename", sa.String(255), nullable=False), sa.Column("content_type", sa.String(100), nullable=False), sa.Column("size_bytes", sa.Integer(), nullable=False), sa.Column("sha256", sa.String(64), nullable=False), sa.Column("processing_status", sa.String(32), nullable=False))
    table("student_facts", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False), sa.Column("document_id", sa.Uuid(), sa.ForeignKey("uploaded_documents.id", ondelete="SET NULL")), sa.Column("field_name", sa.String(100), nullable=False), sa.Column("value", sa.JSON(), nullable=False), sa.Column("confidence", sa.Float(), nullable=False))
    table("source_records", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("opportunity_id", sa.Uuid(), sa.ForeignKey("research_opportunities.id", ondelete="CASCADE"), nullable=False), sa.Column("canonical_url", sa.String(2048), unique=True, nullable=False), sa.Column("host", sa.String(255), nullable=False), sa.Column("title", sa.String(500), nullable=False), sa.Column("http_status", sa.Integer()), sa.Column("verification_state", sa.String(32), nullable=False), sa.Column("excerpt", sa.Text(), nullable=False))
    table("field_evidence", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("source_id", sa.Uuid(), sa.ForeignKey("source_records.id", ondelete="CASCADE"), nullable=False), sa.Column("field_name", sa.String(100), nullable=False), sa.Column("extracted_value", sa.Text(), nullable=False), sa.Column("exact_quote", sa.Text(), nullable=False), sa.Column("verification_state", sa.String(32), nullable=False))
    table("eligibility_assessments", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("workflow_id", sa.Uuid(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("opportunity_id", sa.Uuid(), sa.ForeignKey("research_opportunities.id", ondelete="CASCADE"), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("evidence", sa.JSON(), nullable=False))
    table("match_scores", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("workflow_id", sa.Uuid(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("opportunity_id", sa.Uuid(), sa.ForeignKey("research_opportunities.id", ondelete="CASCADE"), nullable=False), sa.Column("scoring_version", sa.String(32), nullable=False), sa.Column("total_score", sa.Float(), nullable=False), sa.Column("breakdown", sa.JSON(), nullable=False))
    table("application_drafts", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("workflow_id", sa.Uuid(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("opportunity_id", sa.Uuid(), sa.ForeignKey("research_opportunities.id", ondelete="RESTRICT"), nullable=False), sa.Column("version", sa.Integer(), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("provenance", sa.JSON(), nullable=False))
    table("audit_events", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("action", sa.String(100), nullable=False), sa.Column("target_type", sa.String(100), nullable=False), sa.Column("target_id", sa.String(64), nullable=False), sa.Column("metadata_json", sa.JSON(), nullable=False))
def downgrade():
    for name in ["audit_events","application_drafts","match_scores","eligibility_assessments","field_evidence","source_records","student_facts","uploaded_documents"]: op.drop_table(name)
