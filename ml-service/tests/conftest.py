import os
os.environ['DEBUG'] = 'true'
os.environ['INTERNAL_SERVICE_SECRET'] = 'test-secret'
os.environ['BACKEND_URL'] = 'http://test-backend:8000'
os.environ['MODELS_DIR'] = '/tmp/test_models'