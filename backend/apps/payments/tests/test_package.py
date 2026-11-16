def test_payments_package_imports():
    import apps.payments as app

    assert app.__name__ == "apps.payments"
