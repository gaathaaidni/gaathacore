"""Add versioned legal documents and acceptance records.

Revision ID: 20260911_legal_consent
Revises: 20260911_appr_rej_reason
Create Date: 2026-09-11
"""

from datetime import date

from alembic import op
import sqlalchemy as sa

revision = "20260911_legal_consent"
down_revision = "20260911_appr_rej_reason"
branch_labels = None
depends_on = None


DOCUMENTS = [
    ("terms", "Terms & Conditions", "1.0", "Terms and conditions for using Gaatha Suite."),
    ("privacy", "Privacy Policy", "1.0", "How Gaatha Suite processes account and business data."),
    ("cookies", "Cookie Policy", "1.0", "How Gaatha Suite uses cookies and similar technologies."),
    ("user-agreement", "User Agreement", "1.0", "Rules for authorized users of an organization account."),
    ("acceptable-use", "Acceptable Use Policy", "1.0", "Prohibited and permitted uses of the service."),
    ("data-retention", "Data Retention Policy", "1.0", "The current technical approach to retaining account data."),
    ("account-deletion", "Account and Data Deletion", "1.0", "How account deletion and data deletion requests are handled."),
]


def upgrade():
    op.create_table(
        "legal_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_legal_documents_slug"),
    )
    op.create_index("ix_legal_documents_slug", "legal_documents", ["slug"])
    op.create_index("ix_legal_documents_published", "legal_documents", ["published"])

    op.create_table(
        "legal_acceptances",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("legal_documents.id"), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.UniqueConstraint("user_id", "document_id", "version", name="uq_legal_acceptance_version"),
    )
    op.create_index("ix_legal_acceptances_user_id", "legal_acceptances", ["user_id"])
    op.create_index("ix_legal_acceptances_document_id", "legal_acceptances", ["document_id"])
    op.create_index("ix_legal_acceptances_organization_id", "legal_acceptances", ["organization_id"])

    documents = [
        {
            "slug": slug,
            "title": title,
            "version": version,
            "effective_date": date(2026, 9, 11),
            "published": True,
            "content": content,
        }
        for slug, title, version, content in DOCUMENTS
    ]
    op.bulk_insert(sa.table(
        "legal_documents",
        sa.column("slug", sa.String),
        sa.column("title", sa.String),
        sa.column("version", sa.String),
        sa.column("effective_date", sa.Date),
        sa.column("published", sa.Boolean),
        sa.column("content", sa.Text),
    ), documents)


def downgrade():
    op.drop_index("ix_legal_acceptances_organization_id", table_name="legal_acceptances")
    op.drop_index("ix_legal_acceptances_document_id", table_name="legal_acceptances")
    op.drop_index("ix_legal_acceptances_user_id", table_name="legal_acceptances")
    op.drop_table("legal_acceptances")
    op.drop_index("ix_legal_documents_published", table_name="legal_documents")
    op.drop_index("ix_legal_documents_slug", table_name="legal_documents")
    op.drop_table("legal_documents")
