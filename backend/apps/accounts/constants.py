"""Centralized role code identifiers for ILMDAS RBAC."""

ROLE_SYSTEM_ADMINISTRATOR = "system_administrator"
ROLE_LIBRARIAN = "librarian"
ROLE_DIGITAL_ARCHIVIST = "digital_archivist"
ROLE_JOURNAL_EDITOR = "journal_editor"
ROLE_MEMBER = "member"
ROLE_MANAGER = "manager"
ROLE_INTEGRATION_ADMINISTRATOR = "integration_administrator"

ALL_ROLE_CODES = [
    ROLE_SYSTEM_ADMINISTRATOR,
    ROLE_LIBRARIAN,
    ROLE_DIGITAL_ARCHIVIST,
    ROLE_JOURNAL_EDITOR,
    ROLE_MEMBER,
    ROLE_MANAGER,
    ROLE_INTEGRATION_ADMINISTRATOR,
]

ROLE_NAMES = {
    ROLE_SYSTEM_ADMINISTRATOR: "System Administrator",
    ROLE_LIBRARIAN: "Librarian",
    ROLE_DIGITAL_ARCHIVIST: "Digital Archivist",
    ROLE_JOURNAL_EDITOR: "Journal Editor",
    ROLE_MEMBER: "Member",
    ROLE_MANAGER: "Manager",
    ROLE_INTEGRATION_ADMINISTRATOR: "Integration Administrator",
}

ROLE_DESCRIPTIONS = {
    ROLE_SYSTEM_ADMINISTRATOR: "Full system administration including role management.",
    ROLE_LIBRARIAN: "Catalogue and circulation operations.",
    ROLE_DIGITAL_ARCHIVIST: "Digital object and archive management.",
    ROLE_JOURNAL_EDITOR: "Journal publishing operations.",
    ROLE_MEMBER: "Standard member access to public and member features.",
    ROLE_MANAGER: "Management oversight across modules.",
    ROLE_INTEGRATION_ADMINISTRATOR: "Integration and external system configuration.",
}
