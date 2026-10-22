import pytest
from app import create_app, db, Category, Product

@pytest.fixture()
def app():
    app=create_app({'TESTING':True,'WTF_CSRF_ENABLED':False,'SQLALCHEMY_DATABASE_URI':'sqlite:///:memory:','SECRET_KEY':'test-secret'})
    with app.app_context():
        db.create_all()
        cat=Category(name='Dairy and Eggs',slug='dairy-and-eggs'); db.session.add(cat); db.session.flush()
        db.session.add_all([Product(name='Whole Milk',brand='Amul',category_id=cat.id,price=60,stock=10,pack_size='1 L'),Product(name='Oat Milk',brand='Daily',category_id=cat.id,price=80,stock=0,pack_size='1 L')]); db.session.commit()
    yield app
    with app.app_context(): db.drop_all()

@pytest.fixture()
def client(app): return app.test_client()

@pytest.fixture()
def customer(client):
    client.post('/register',data={'name':'Test Person','email':'test@example.com','password':'strongpassword9','confirm':'strongpassword9','terms':'on'})
    client.post('/login',data={'email':'test@example.com','password':'strongpassword9'})
    return client
