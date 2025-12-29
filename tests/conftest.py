import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-real",
        action="store_true",
        default=False,
        help="Run tests that hit real APIs.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "real: marks tests that use real API calls")
    config.addinivalue_line("markers", "mock: marks tests that use mocked API calls")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-real"):
        return

    skip_real = pytest.mark.skip(reason="need --run-real to run")
    for item in items:
        if "real" in item.keywords:
            item.add_marker(skip_real)
