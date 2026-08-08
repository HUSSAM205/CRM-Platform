"""Static permission catalog and system role -> permission mapping.

This is the single source of truth for permission codes: both the FastAPI
routes (via require_permission) and the Alembic seed migration
(alembic/versions/..._seed_permissions_and_roles.py) import from here, so
the two can never drift apart.
"""


class Permissions:
    ADMIN_ACCESS = "admin.access"
    USER_INVITE = "user.invite"
    USER_MANAGE = "user.manage"
    ROLE_MANAGE = "role.manage"
    ORG_MANAGE = "org.manage"
    DOCUMENT_CREATE = "document.create"
    DOCUMENT_VIEW = "document.view"
    DOCUMENT_EDIT = "document.edit"
    DOCUMENT_DELETE = "document.delete"
    DOCUMENT_SHARE = "document.share"
    COMMENT_CREATE = "comment.create"
    COMMENT_DELETE_ANY = "comment.delete_any"
    MESSAGE_SEND = "message.send"
    AUDIT_VIEW = "audit.view"


PERMISSION_DESCRIPTIONS: dict[str, str] = {
    Permissions.ADMIN_ACCESS: "Access the admin portal",
    Permissions.USER_INVITE: "Invite new users to the organization",
    Permissions.USER_MANAGE: "Manage (deactivate, edit) organization users",
    Permissions.ROLE_MANAGE: "Manage roles and role assignments",
    Permissions.ORG_MANAGE: "Manage organization-wide settings",
    Permissions.DOCUMENT_CREATE: "Upload new documents",
    Permissions.DOCUMENT_VIEW: "View documents shared with you",
    Permissions.DOCUMENT_EDIT: "Edit document metadata and upload new versions",
    Permissions.DOCUMENT_DELETE: "Delete documents",
    Permissions.DOCUMENT_SHARE: "Share documents with other users or roles",
    Permissions.COMMENT_CREATE: "Comment on documents",
    Permissions.COMMENT_DELETE_ANY: "Delete any comment, not just your own",
    Permissions.MESSAGE_SEND: "Send direct messages and channel messages",
    Permissions.AUDIT_VIEW: "View the organization audit log",
}

SYSTEM_ROLE_DESCRIPTIONS: dict[str, str] = {
    "admin": "Full access, including the admin portal and organization settings",
    "manager": "Manage users, documents, and view the audit log",
    "member": "Create and collaborate on documents",
    "viewer": "Read-only access to shared documents",
}

SYSTEM_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": list(PERMISSION_DESCRIPTIONS.keys()),
    "manager": [
        Permissions.USER_INVITE,
        Permissions.USER_MANAGE,
        Permissions.DOCUMENT_CREATE,
        Permissions.DOCUMENT_VIEW,
        Permissions.DOCUMENT_EDIT,
        Permissions.DOCUMENT_DELETE,
        Permissions.DOCUMENT_SHARE,
        Permissions.COMMENT_CREATE,
        Permissions.COMMENT_DELETE_ANY,
        Permissions.MESSAGE_SEND,
        Permissions.AUDIT_VIEW,
    ],
    "member": [
        Permissions.DOCUMENT_CREATE,
        Permissions.DOCUMENT_VIEW,
        Permissions.DOCUMENT_EDIT,
        Permissions.DOCUMENT_SHARE,
        Permissions.COMMENT_CREATE,
        Permissions.MESSAGE_SEND,
    ],
    "viewer": [
        Permissions.DOCUMENT_VIEW,
        Permissions.COMMENT_CREATE,
        Permissions.MESSAGE_SEND,
    ],
}
