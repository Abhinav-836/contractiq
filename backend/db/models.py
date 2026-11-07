# db/models.py
"""Import every model module so all tables register on Base.metadata."""


def import_all_models() -> None:
    import modules.users.models        # noqa: F401
    import modules.contracts.models    # noqa: F401
    import modules.analysis.models     # noqa: F401
    import modules.obligations.models  # noqa: F401
    import modules.alerts.models       # noqa: F401
    import modules.workspaces.models   # noqa: F401
    import modules.approvals.models    # noqa: F401
    import modules.signatures.models   # noqa: F401
