"""Observe deployed source without exposing credentials or changing API payloads."""
import hashlib
import secrets

from fastapi.testclient import TestClient
import pytest

from fridgely_app.host import create_app


@pytest.mark.parametrize('valid_revision', [True, False])
def test_public_revision_is_validated_platform_metadata_not_request_input(tmp_path, monkeypatch, valid_revision):
    revision = hashlib.sha1(b'synthetic-public-revision').hexdigest()
    if valid_revision:
        monkeypatch.setenv('RENDER_GIT_COMMIT', revision)
    else:
        monkeypatch.setenv('RENDER_GIT_COMMIT', 'not-a-git-revision')
    app = create_app(database_url=f'sqlite:///{tmp_path / "release.db"}',
        jwt_secret=secrets.token_urlsafe(48), frontend_dir=tmp_path)
    with TestClient(app) as client:
        for path in ['/api/health', '/api/inventory', '/missing']:
            response = client.get(path, headers={'X-Fridgely-Revision': 'request-must-not-choose-source'})
            if valid_revision:
                assert response.headers.get('X-Fridgely-Revision') == revision
            else:
                assert 'X-Fridgely-Revision' not in response.headers
    app.state.engine.dispose()
