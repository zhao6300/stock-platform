def test_no_live_broker_order_package_boundary_is_declared() -> None:
    module_dir = __import__("pathlib").Path("src") / "stock_platform"
    files = list(module_dir.glob("**/*.py"))

    assert not any(path.name == "broker.py" for path in files)
    assert not any(path.name == "orders.py" for path in files)
    assert not any(path.name == "live_trading.py" for path in files)
