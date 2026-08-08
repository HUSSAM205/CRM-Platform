"""seed permission catalog and system roles

Revision ID: df6598cd03a6
Revises: 93cf6720697c
Create Date: 2026-08-08 23:52:43.462414

"""
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.permissions import PERMISSION_DESCRIPTIONS, SYSTEM_ROLE_DESCRIPTIONS, SYSTEM_ROLE_PERMISSIONS

# revision identifiers, used by Alembic.
revision: str = 'df6598cd03a6'
down_revision: Union[str, Sequence[str], None] = '93cf6720697c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    permission_ids: dict[str, str] = {}
    for code, description in PERMISSION_DESCRIPTIONS.items():
        pid = str(uuid.uuid4())
        permission_ids[code] = pid
        conn.execute(
            sa.text("INSERT INTO permissions (id, code, description) VALUES (:id, :code, :description)"),
            {"id": pid, "code": code, "description": description},
        )

    role_ids: dict[str, str] = {}
    for role_name, description in SYSTEM_ROLE_DESCRIPTIONS.items():
        rid = str(uuid.uuid4())
        role_ids[role_name] = rid
        conn.execute(
            sa.text(
                "INSERT INTO roles (id, organization_id, name, description, is_system) "
                "VALUES (:id, NULL, :name, :description, true)"
            ),
            {"id": rid, "name": role_name, "description": description},
        )

    for role_name, codes in SYSTEM_ROLE_PERMISSIONS.items():
        for code in codes:
            conn.execute(
                sa.text("INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)"),
                {"role_id": role_ids[role_name], "permission_id": permission_ids[code]},
            )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM role_permissions"))
    conn.execute(sa.text("DELETE FROM roles WHERE is_system = true"))
    conn.execute(sa.text("DELETE FROM permissions"))
