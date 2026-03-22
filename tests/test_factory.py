'''
Name: test_factory.py
Description: factory tests
Authors: Brinley Hull & Anakha Krishna
Other sources: Flask tutorial flask.com
Created: 3/22/2026
Last modified: 3/22/2026
'''

from vgle import create_app


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello')
    assert response.data == b'Hello, World!'