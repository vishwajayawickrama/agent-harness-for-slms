from importlib.metadata import version


def test_package_version() -> None:
    assert version("agent-harness-for-slms") == "0.1.0"
