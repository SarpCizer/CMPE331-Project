"""Deliberate CI failure for the isolated branch-protection test PR #75."""


def test_main_protection_rejects_failing_required_backend_check():
    raise AssertionError("Issue #22 probe: deliberately fail the required backend check")
