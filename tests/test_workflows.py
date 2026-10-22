import json
from app import db, User, Product, WishlistItem, Notification, Order
from werkzeug.security import check_password_hash, generate_password_hash

def test_registration_hash_and_duplicate(client,app):
    r=client.post('/register',data={'name':'Test Person','email':'test@example.com','password':'strongpassword9','confirm':'strongpassword9','terms':'on'},follow_redirects=True)
    assert b'Account created' in r.data
    with app.app_context():
        u=User.query.filter_by(email='test@example.com').one(); assert check_password_hash(u.password_hash,'strongpassword9'); assert u.password_hash!='strongpassword9'
    r=client.post('/register',data={'name':'Test Person','email':'test@example.com','password':'strongpassword9','confirm':'strongpassword9','terms':'on'},follow_redirects=True)
    assert b'already exists' in r.data

def test_search_partial_and_no_results(client):
    assert client.get('/api/products?q=milk').json['total']==2
    r=client.get('/api/products?q=not-a-product'); assert r.json['items']==[]

def test_cart_persistence_and_stock_validation(customer):
    assert customer.get('/api/cart').status_code==200
    assert customer.post('/api/cart',json={'product_id':1,'quantity':2}).status_code==200
    customer.post('/api/cart',json={'product_id':1,'quantity':2})
    assert customer.get('/api/cart').json['items'][0]['quantity']==4
    assert customer.patch('/api/cart/1',json={'quantity':11}).status_code==409
    assert customer.delete('/api/cart/1').status_code==200

def test_wishlist_back_in_stock_and_admin_guard(customer,app):
    assert customer.post('/api/wishlist',json={'product_id':2}).status_code==200
    assert customer.get('/api/notifications').json['unread']==0
    assert customer.get('/api/admin/stats').status_code==403
    with app.app_context():
        cat=Product.query.get(1).category_id
        admin=User(name='Admin',email='admin@example.com',password_hash=generate_password_hash('securepassword8'),role='admin'); db.session.add(admin); db.session.commit(); aid=admin.id
    customer.post('/logout')
    with customer.session_transaction() as s: s['uid']=aid
    assert customer.put('/api/admin/products/2',json={'name':'Oat Milk','brand':'Daily','description':'','category_id':1,'price':'80','discount_percent':0,'stock':5,'active':True}).status_code==200
    customer.post('/logout')
    customer.post('/login',data={'email':'test@example.com','password':'strongpassword9'})
    notes=customer.get('/api/notifications').json
    assert notes['unread']==1 and 'back in stock' in notes['items'][0]['message']

def test_cod_order_and_online_payment_block(customer,app):
    customer.post('/api/cart',json={'product_id':1,'quantity':2})
    bad=customer.post('/checkout',json={'address':'123 Fresh Street','phone':'1234567890','payment_method':'online'})
    assert bad.status_code==400 and 'disabled' in bad.json['error']
    ok=customer.post('/checkout',json={'address':'123 Fresh Street','phone':'1234567890','payment_method':'cod'})
    assert ok.status_code==201
    with app.app_context():
        o=Order.query.one(); assert o.payment_status=='Not Paid' and o.total==120
        assert Product.query.get(1).stock==8
        assert len(o.items)==1 and o.items[0].unit_price==60

def test_unauthenticated_and_customer_order_scope(client):
    assert client.get('/api/cart').status_code==401
    assert client.get('/admin').status_code==302
