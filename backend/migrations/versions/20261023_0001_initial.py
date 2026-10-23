"""initial authoritative scholarship tables

Revision ID: 20261023_0001
"""
from alembic import op
import sqlalchemy as sa

revision = "20261023_0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("external_subject", sa.String(255), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_users_external_subject", "users", ["external_subject"], unique=True)
    op.create_table("student_profiles", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("data", sa.JSON(), nullable=False), sa.Column("confirmed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_student_profiles_user_id", "student_profiles", ["user_id"])
    op.create_table("workflow_runs", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("profile_id", sa.Uuid(), sa.ForeignKey("student_profiles.id", ondelete="RESTRICT"), nullable=False), sa.Column("idempotency_key", sa.String(128), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("current_node", sa.String(64)), sa.Column("failure_reason", sa.Text()), sa.Column("result", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("user_id", "idempotency_key", name="uq_workflow_user_key"))
    op.create_index("ix_workflow_runs_user_id", "workflow_runs", ["user_id"]); op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"])
    op.create_table("agent_events", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("workflow_id", sa.Uuid(), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False), sa.Column("node", sa.String(64), nullable=False), sa.Column("event_type", sa.String(32), nullable=False), sa.Column("detail", sa.Text(), nullable=False), sa.Column("attempt", sa.Integer(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_events_workflow_created", "agent_events", ["workflow_id", "created_at"])
    op.create_table("research_opportunities", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("provider", sa.String(255), nullable=False), sa.Column("program_identity", sa.String(255), nullable=False), sa.Column("degree_level", sa.String(64), nullable=False), sa.Column("application_cycle", sa.String(64), nullable=False), sa.Column("data", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("provider", "program_identity", "degree_level", "application_cycle", name="uq_opportunity_cycle"))
    op.create_index("ix_research_opportunities_provider", "research_opportunities", ["provider"])

def downgrade():
    op.drop_table("research_opportunities"); op.drop_table("agent_events"); op.drop_table("workflow_runs"); op.drop_table("student_profiles"); op.drop_table("users")
