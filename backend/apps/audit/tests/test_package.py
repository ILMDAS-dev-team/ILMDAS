def test_audit_package_imports():
    import apps.audit as app

    assert app.__name__ == "apps.audit"
