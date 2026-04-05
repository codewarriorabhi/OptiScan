import os
import sys
import tempfile
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
from app import app, allowed_file, validate_file_type


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAllowedFile:
    def test_allowed_extensions(self):
        assert allowed_file('image.jpg') == True
        assert allowed_file('image.png') == True
        assert allowed_file('document.pdf') == False
        assert allowed_file('image.JPEG') == True

    def test_no_extension(self):
        assert allowed_file('image') == False

    def test_empty_filename(self):
        assert allowed_file('') == False


class TestIndex:
    def test_index_page(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b'OptiScan' in response.data


class TestExtract:
    def test_no_file(self, client):
        response = client.post('/extract')
        assert response.status_code == 400
        assert b'No file provided' in response.data

    def test_empty_filename(self, client):
        data = {
            'file': (BytesIO(b''), '')
        }
        response = client.post('/extract', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        assert b'No file selected' in response.data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
