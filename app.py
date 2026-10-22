import os, secrets, logging
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
from flask import Flask, jsonify, request, session, redirect, url_for, render_template, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_, func
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

db = SQLAlchemy()
csrf = CSRFProtect()

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),nullable=False); email=db.Column(db.String(255),unique=True,nullable=False,index=True); phone=db.Column(db.String(30)); password_hash=db.Column(db.String(255),nullable=False); role=db.Column(db.String(20),nullable=False,default='customer'); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Category(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(80),unique=True,nullable=False); slug=db.Column(db.String(100),unique=True,nullable=False)
class Product(db.Model):
    id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(160),nullable=False,index=True); description=db.Column(db.Text,default=''); brand=db.Column(db.String(100),default=''); category_id=db.Column(db.Integer,db.ForeignKey('category.id'),nullable=False); price=db.Column(db.Numeric(10,2),nullable=False); discount_percent=db.Column(db.Numeric(5,2),default=0); image_url=db.Column(db.String(500),default=''); pack_size=db.Column(db.String(80),default=''); stock=db.Column(db.Integer,default=0,nullable=False); active=db.Column(db.Boolean,default=True,nullable=False); featured=db.Column(db.Boolean,default=False); created_at=db.Column(db.DateTime,default=datetime.utcnow); category=db.relationship('Category')
    @property
    def final_price(self): return (Decimal(self.price)*(Decimal(100)-Decimal(self.discount_percent or 0))/Decimal(100)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
class CartItem(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id',ondelete='CASCADE'),nullable=False); product_id=db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False); quantity=db.Column(db.Integer,nullable=False,default=1); product=db.relationship('Product'); __table_args__=(db.UniqueConstraint('user_id','product_id'),)
class WishlistItem(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id',ondelete='CASCADE'),nullable=False); product_id=db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False); product=db.relationship('Product'); __table_args__=(db.UniqueConstraint('user_id','product_id'),)
class Notification(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id',ondelete='CASCADE'),nullable=False,index=True); product_id=db.Column(db.Integer,db.ForeignKey('product.id'),nullable=False); message=db.Column(db.String(300),nullable=False); read=db.Column(db.Boolean,default=False,nullable=False); event_key=db.Column(db.String(100),unique=True,nullable=False); created_at=db.Column(db.DateTime,default=datetime.utcnow); product=db.relationship('Product')
class Order(db.Model):
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False,index=True); created_at=db.Column(db.DateTime,default=datetime.utcnow); address=db.Column(db.Text,nullable=False); phone=db.Column(db.String(30),nullable=False); subtotal=db.Column(db.Numeric(10,2),nullable=False); discount=db.Column(db.Numeric(10,2),nullable=False,default=0); delivery_fee=db.Column(db.Numeric(10,2),nullable=False,default=0); total=db.Column(db.Numeric(10,2),nullable=False); payment_method=db.Column(db.String(30),nullable=False); payment_status=db.Column(db.String(30),nullable=False,default='Not Paid'); status=db.Column(db.String(30),nullable=False,default='Pending'); user=db.relationship('User'); items=db.relationship('OrderItem',cascade='all, delete-orphan')
class OrderItem(db.Model):
    id=db.Column(db.Integer,primary_key=True); order_id=db.Column(db.Integer,db.ForeignKey('order.id',ondelete='CASCADE'),nullable=False); product_id=db.Column(db.Integer,db.ForeignKey('product.id'),nullable=True); product_name=db.Column(db.String(160),nullable=False); unit_price=db.Column(db.Numeric(10,2),nullable=False); quantity=db.Column(db.Integer,nullable=False); item_subtotal=db.Column(db.Numeric(10,2),nullable=False)

def create_app(test_config=None):
    app=Flask(__name__); app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or secrets.token_hex(32), SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','mysql+pymysql://root:@127.0.0.1:3306/groczy_db?charset=utf8mb4'), SQLALCHEMY_TRACK_MODIFICATIONS=False, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.getenv('COOKIE_SECURE','0')=='1', MAX_CONTENT_LENGTH=3*1024*1024)
    if test_config: app.config.update(test_config)
    db.init_app(app); csrf.init_app(app); logging.basicConfig(level=logging.INFO)
    @app.context_processor
    def inject():
        u=current_user(); return {'current_user':u,'cart_count':CartItem.query.filter_by(user_id=u.id).with_entities(func.coalesce(func.sum(CartItem.quantity),0)).scalar() if u else 0,'unread_count':Notification.query.filter_by(user_id=u.id,read=False).count() if u else 0}
    def api_error(msg,status): return jsonify({'ok':False,'error':msg}),status
    def current_user(): return db.session.get(User,session.get('uid')) if session.get('uid') else None
    def login_required(fn):
        @wraps(fn)
        def w(*a,**kw):
            if not current_user():
                if request.path.startswith('/api/'): return api_error('Sign in required.',401)
                return redirect(url_for('login',next=request.path))
            return fn(*a,**kw)
        return w
    def admin_required(fn):
        @wraps(fn)
        def w(*a,**kw):
            u=current_user()
            if not u: return api_error('Sign in required.',401) if request.path.startswith('/api/') else redirect(url_for('login'))
            if u.role!='admin': return api_error('Administrator access required.',403) if request.path.startswith('/api/') else abort(403)
            return fn(*a,**kw)
        return w
    def product_json(p): return {'id':p.id,'name':p.name,'brand':p.brand,'description':p.description,'category':p.category.name,'category_id':p.category_id,'price':str(p.price),'discount_percent':str(p.discount_percent),'final_price':str(p.final_price),'image_url':p.image_url,'pack_size':p.pack_size,'stock':p.stock,'available':p.active and p.stock>0,'active':p.active,'featured':p.featured}
    @app.get('/')
    def home():
        categories=Category.query.order_by(Category.name).all()
        grouped_products=[(category,Product.query.filter_by(category_id=category.id,active=True).order_by(Product.featured.desc(),Product.name.asc()).all()) for category in categories]
        hero_products=Product.query.filter(Product.active.is_(True),Product.stock>0).order_by(Product.featured.desc(),Product.created_at.desc()).limit(2).all()
        return render_template('index.html',grouped_products=grouped_products,categories=categories,hero_products=hero_products)
    @app.get('/products')
    def catalog(): return render_template('products.html',categories=Category.query.order_by(Category.name).all())
    @app.get('/budget-shopping')
    def budget_shopping(): return render_template('budget_shopping.html')
    @app.get('/product/<int:product_id>')
    def product_page(product_id):
        p=db.session.get(Product,product_id)
        if not p or not p.active: abort(404)
        similar=Product.query.filter(Product.category_id==p.category_id,Product.id!=p.id,Product.active.is_(True)).limit(4).all(); return render_template('detail.html',product=p,similar=similar)
    @app.get('/about')
    def about(): return render_template('info.html',title='About Groczy',body='Groczy helps you make smart choices with fresh groceries, transparent prices, and practical recommendations.')
    @app.get('/contact')
    def contact(): return render_template('info.html',title='Contact',body='For this local demonstration, contact support through your project administrator.')
    @app.route('/register',methods=['GET','POST'])
    def register():
        if request.method=='POST':
            name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); phone=request.form.get('phone','').strip(); pw=request.form.get('password',''); confirm=request.form.get('confirm','')
            errors=[]
            if len(name)<2: errors.append('Enter your full name.')
            if '@' not in email or len(email)>255: errors.append('Enter a valid email address.')
            if len(pw)<10 or not any(c.isalpha() for c in pw) or not any(c.isdigit() for c in pw): errors.append('Password must be at least 10 characters and include a letter and number.')
            if pw!=confirm: errors.append('Passwords do not match.')
            if not request.form.get('terms'): errors.append('Accept the terms to continue.')
            if User.query.filter_by(email=email).first(): errors.append('An account with that email already exists.')
            if errors:
                for e in errors: flash(e,'error')
            else:
                db.session.add(User(name=name,email=email,phone=phone,password_hash=generate_password_hash(pw))); db.session.commit(); flash('Account created. Please sign in.','success'); return redirect(url_for('login'))
        return render_template('auth.html',mode='Register')
    @app.route('/login',methods=['GET','POST'])
    def login():
        if request.method=='POST':
            u=User.query.filter_by(email=request.form.get('email','').strip().lower()).first()
            if not u or not check_password_hash(u.password_hash,request.form.get('password','')): flash('Invalid email or password.','error')
            else:
                session.clear(); session['uid']=u.id; session.permanent=bool(request.form.get('remember'))
                target=request.args.get('next','')
                if u.role!='admin' and target.startswith('/') and not target.startswith('//') and '\\' not in target: return redirect(target)
                return redirect(url_for('admin') if u.role=='admin' else url_for('home'))
        return render_template('auth.html',mode='Login')
    @app.post('/logout')
    def logout(): session.clear(); return redirect(url_for('home'))
    @app.get('/api/products')
    def api_products():
        q=request.args.get('q','').strip(); query=Product.query.join(Category).filter(Product.active.is_(True));
        if q: like='%'+q+'%'; query=query.filter(or_(Product.name.ilike(like),Product.brand.ilike(like),Product.description.ilike(like),Category.name.ilike(like)))
        cat=request.args.get('category'); brand=request.args.get('brand'); available=request.args.get('available');
        if cat: query=query.filter(Category.slug==cat)
        if brand: query=query.filter(Product.brand.ilike('%'+brand+'%'))
        if available=='1': query=query.filter(Product.stock>0)
        if request.args.get('min'): query=query.filter(Product.price>=request.args.get('min'))
        if request.args.get('max'): query=query.filter(Product.price<=request.args.get('max'))
        sort=request.args.get('sort','newest')
        if sort=='popular':
            popularity=db.session.query(OrderItem.product_id,func.sum(OrderItem.quantity).label('units')).group_by(OrderItem.product_id).subquery()
            query=query.outerjoin(popularity,Product.id==popularity.c.product_id).order_by(func.coalesce(popularity.c.units,0).desc(),Product.name.asc())
        else: query=query.order_by(Product.price.asc() if sort=='price_asc' else Product.price.desc() if sort=='price_desc' else Product.name.asc() if sort=='name' else Product.created_at.desc())
        page=max(1,request.args.get('page',1,type=int)); pagination=query.paginate(page=page,per_page=12,error_out=False); return jsonify({'ok':True,'items':[product_json(p) for p in pagination.items],'page':page,'pages':pagination.pages,'total':pagination.total})
    @app.get('/api/products/<int:product_id>')
    def api_product(product_id):
        p=db.session.get(Product,product_id); return (jsonify({'ok':True,'item':product_json(p)}) if p and p.active else api_error('Product not found.',404))
    @app.get('/api/categories')
    def api_categories(): return jsonify({'ok':True,'items':[{'id':c.id,'name':c.name,'slug':c.slug} for c in Category.query.order_by(Category.name)]})
    @app.get('/api/csrf-token')
    def csrf_token_api():
        # Refresh the signed double-submit token for long-lived tabs before writes.
        from flask_wtf.csrf import generate_csrf
        return jsonify({'ok':True,'csrf_token':generate_csrf()})
    @app.get('/api/recommendations')
    def recommendations():
        u=current_user(); query=Product.query.filter(Product.active.is_(True),Product.stock>0)
        if u:
            bought=db.session.query(Product.category_id,func.count(OrderItem.id).label('n')).join(OrderItem,OrderItem.product_id==Product.id).join(Order,Order.id==OrderItem.order_id).filter(Order.user_id==u.id).group_by(Product.category_id).order_by(func.count(OrderItem.id).desc()).first()
            if bought: query=query.filter(Product.category_id==bought[0])
        rows=query.order_by(Product.featured.desc(),Product.created_at.desc()).limit(8).all()
        if not rows: rows=Product.query.filter(Product.active.is_(True),Product.stock>0).order_by(Product.featured.desc(),Product.created_at.desc()).limit(8).all()
        return jsonify({'ok':True,'heading':'Recommended for You' if u else 'Popular Picks','items':[product_json(p) for p in rows]})
    @app.post('/api/budget/generate')
    def generate_budget_list():
        data=request.get_json(silent=True) or {}
        try:
            budget=Decimal(str(data.get('budget','')))
            if not budget.is_finite() or budget<=0 or budget>Decimal('100000'):
                raise ValueError()
        except (ArithmeticError,ValueError,TypeError):
            return api_error('Enter a budget greater than ₹0 and no more than ₹100,000.',400)
        preference=data.get('preference','essentials')
        if preference not in {'essentials','healthy','family','lowest_price'}:
            return api_error('Choose a valid shopping preference.',400)
        category_groups={
            'produce':['Fruits','Vegetables'],
            'dairy':['Dairy and Eggs'],
            'grains':['Rice and Grains','Pulses and Lentils'],
            'snacks':['Snacks'],
            'household':['Household Essentials'],
        }
        chosen_group=data.get('category','')
        if chosen_group and chosen_group not in category_groups:
            return api_error('Choose a valid grocery category.',400)
        query=Product.query.join(Category).filter(Product.active.is_(True),Product.stock>0)
        if chosen_group:
            query=query.filter(Category.name.in_(category_groups[chosen_group]))
        candidates=query.all()
        if not candidates:
            return jsonify({'ok':True,'items':[],'budget':str(budget.quantize(Decimal('.01'))),'total':'0.00','remaining':str(budget.quantize(Decimal('.01'))),'message':'No in-stock products match those choices. Try another category or preference.'})
        rank_groups={
            'essentials':['produce','dairy','grains','household','snacks'],
            'healthy':['produce','grains','dairy','snacks','household'],
            'family':['grains','dairy','produce','bakery','snacks','household'],
            'lowest_price':[],
        }
        def product_group(product):
            name=product.category.name
            return next((group for group,names in category_groups.items() if name in names),'bakery' if name=='Bakery' else 'household')
        pref_order=rank_groups[preference]
        variant=max(0,data.get('variant',0) if isinstance(data.get('variant',0),int) else 0)
        if preference=='lowest_price':
            candidates.sort(key=lambda p:(p.final_price,(p.id+variant)%max(1,len(candidates)),p.name.casefold()))
        else:
            candidates.sort(key=lambda p:(pref_order.index(product_group(p)) if product_group(p) in pref_order else len(pref_order),p.final_price,(p.id+variant)%max(1,len(candidates)),p.name.casefold()))
        excluded=data.get('exclude_ids',[])
        if isinstance(excluded,list):
            excluded_ids={int(value) for value in excluded if str(value).isdigit()}
            alternatives=[p for p in candidates if p.id not in excluded_ids]
            if alternatives: candidates=alternatives
        remaining=budget.quantize(Decimal('.01')); selected={}
        # First pass tries to include a small, varied basket across ranked categories.
        seen_groups=set()
        for product in candidates:
            group=product_group(product)
            if group in seen_groups or product.final_price>remaining: continue
            selected[product.id]=[product,1]
            remaining-=product.final_price
            seen_groups.add(group)
        # Fill unused budget with the best remaining eligible options, never overshooting.
        for product in candidates:
            if product.id in selected or product.final_price>remaining: continue
            selected[product.id]=[product,1]
            remaining-=product.final_price
        # Add extra units where budget and stock permit, cycling in preference order.
        while True:
            added=False
            for product in candidates:
                if product.final_price>remaining: continue
                row=selected.get(product.id)
                if row and row[1]>=product.stock: continue
                if row: row[1]+=1
                else: selected[product.id]=[product,1]
                remaining-=product.final_price; added=True
            if not added: break
        items=[]
        for product,quantity in selected.values():
            unit=product.final_price
            items.append({'product_id':product.id,'name':product.name,'image_url':product.image_url,'category':product.category.name,'quantity':quantity,'unit_price':str(unit),'line_total':str(unit*quantity),'stock':product.stock})
        total=budget.quantize(Decimal('.01'))-remaining
        return jsonify({'ok':True,'items':items,'budget':str(budget.quantize(Decimal('.01'))),'total':str(total),'remaining':str(remaining),'message':'' if items else 'No products fit this budget. Try increasing it or changing your choices.'})
    @app.get('/cart')
    @login_required
    def cart(): return render_template('cart.html')
    def cart_data(uid):
        items=CartItem.query.filter_by(user_id=uid).all(); rows=[]; total=Decimal('0.00')
        for i in items:
            p=i.product
            if not p: continue
            sub=p.final_price*i.quantity; total+=sub; rows.append({'id':p.id,'name':p.name,'image_url':p.image_url,'price':str(p.final_price),'quantity':i.quantity,'subtotal':str(sub),'stock':p.stock,'available':p.active and p.stock>0})
        return {'items':rows,'count':sum(i['quantity'] for i in rows),'subtotal':str(total),'delivery_fee':'0.00','total':str(total)}
    @app.get('/api/cart')
    @login_required
    def get_cart(): return jsonify({'ok':True,**cart_data(current_user().id)})
    @app.post('/api/cart')
    @login_required
    def add_cart():
        d=request.get_json(silent=True) or {}; p=db.session.get(Product,d.get('product_id')); qty=d.get('quantity',1); u=current_user()
        if not p or not p.active: return api_error('Product unavailable.',404)
        if not isinstance(qty,int) or qty<1: return api_error('Quantity must be a positive whole number.',400)
        item=CartItem.query.filter_by(user_id=u.id,product_id=p.id).first(); newqty=qty+(item.quantity if item else 0)
        if newqty>p.stock: return api_error('Requested quantity exceeds available stock.',409)
        if item: item.quantity=newqty
        else: db.session.add(CartItem(user_id=u.id,product_id=p.id,quantity=qty))
        db.session.commit(); return jsonify({'ok':True,**cart_data(u.id)})
    @app.patch('/api/cart/<int:product_id>')
    @login_required
    def update_cart(product_id):
        d=request.get_json(silent=True) or {}; qty=d.get('quantity'); i=CartItem.query.filter_by(user_id=current_user().id,product_id=product_id).first()
        if not i: return api_error('Cart item not found.',404)
        if not isinstance(qty,int) or qty<1: return api_error('Quantity must be a positive whole number.',400)
        if qty>i.product.stock: return api_error('Requested quantity exceeds available stock.',409)
        i.quantity=qty; db.session.commit(); return jsonify({'ok':True,**cart_data(current_user().id)})
    @app.delete('/api/cart/<int:product_id>')
    @login_required
    def delete_cart(product_id):
        i=CartItem.query.filter_by(user_id=current_user().id,product_id=product_id).first()
        if i: db.session.delete(i); db.session.commit()
        return jsonify({'ok':True,**cart_data(current_user().id)})
    @app.post('/api/budget/add-to-cart')
    @login_required
    def budget_add_to_cart():
        data=request.get_json(silent=True) or {}; uid=current_user().id
        try:
            budget=Decimal(str(data.get('budget','')))
            if not budget.is_finite() or budget<=0 or budget>Decimal('100000'): raise ValueError()
            submitted=data.get('items')
            if not isinstance(submitted,list) or not submitted: return api_error('Your recommended list is empty.',400)
            quantities={}
            for row in submitted:
                pid=row.get('product_id'); qty=row.get('quantity')
                if not isinstance(pid,int) or not isinstance(qty,int) or qty<1: return api_error('Product IDs and quantities must be valid positive whole numbers.',400)
                if pid in quantities: return api_error('Remove duplicate products from your list before adding it.',400)
                quantities[pid]=qty
            products=Product.query.filter(Product.id.in_(quantities)).with_for_update().all()
            by_id={p.id:p for p in products}
            if len(by_id)!=len(quantities): return api_error('One or more products are no longer available.',409)
            total=Decimal('0.00'); cart_rows={i.product_id:i for i in CartItem.query.filter_by(user_id=uid).with_for_update().all()}
            for pid,qty in quantities.items():
                p=by_id[pid]; existing=cart_rows.get(pid); combined=qty+(existing.quantity if existing else 0)
                if not p.active or p.stock<1 or combined>p.stock: return api_error(f'{p.name} is no longer available in the requested quantity.',409)
                total+=p.final_price*qty
            if total>budget: return api_error('Current database prices put this list over your budget. Generate the list again.',409)
            for pid,qty in quantities.items():
                existing=cart_rows.get(pid)
                if existing: existing.quantity+=qty
                else: db.session.add(CartItem(user_id=uid,product_id=pid,quantity=qty))
            db.session.commit()
            return jsonify({'ok':True,'message':'Selected items were added to your cart within the budget.','budget':str(budget),'list_total':str(total),**cart_data(uid)})
        except (ArithmeticError,ValueError,TypeError):
            db.session.rollback(); return api_error('Enter a valid budget and product list.',400)
        except Exception:
            db.session.rollback(); app.logger.exception('Budget list add-to-cart failed'); return api_error('Could not add the list to your cart. Please try again.',500)
    @app.get('/wishlist')
    @login_required
    def wishlist(): return render_template('wishlist.html')
    @app.route('/api/wishlist',methods=['GET','POST'])
    @login_required
    def wishlist_api():
        u=current_user()
        if request.method=='POST':
            d=request.get_json(silent=True) or {}; p=db.session.get(Product,d.get('product_id'))
            if not p: return api_error('Product not found.',404)
            if not WishlistItem.query.filter_by(user_id=u.id,product_id=p.id).first(): db.session.add(WishlistItem(user_id=u.id,product_id=p.id)); db.session.commit()
            return jsonify({'ok':True,'items':[product_json(x.product) for x in WishlistItem.query.filter_by(user_id=u.id).all()]})
        return jsonify({'ok':True,'items':[product_json(x.product) for x in WishlistItem.query.filter_by(user_id=u.id).all()]})
    @app.delete('/api/wishlist/<int:product_id>')
    @login_required
    def wishlist_delete(product_id):
        i=WishlistItem.query.filter_by(user_id=current_user().id,product_id=product_id).first()
        if i: db.session.delete(i); db.session.commit()
        return jsonify({'ok':True})
    @app.post('/api/wishlist/<int:product_id>/cart')
    @login_required
    def wishlist_cart(product_id):
        p=db.session.get(Product,product_id)
        if not p or not p.active or p.stock<1: return api_error('This product is currently unavailable.',409)
        i=CartItem.query.filter_by(user_id=current_user().id,product_id=p.id).first()
        if i: i.quantity+=1
        else: db.session.add(CartItem(user_id=current_user().id,product_id=p.id,quantity=1))
        if i and i.quantity>p.stock: return api_error('Requested quantity exceeds available stock.',409)
        db.session.commit(); return jsonify({'ok':True})
    @app.get('/api/notifications')
    @login_required
    def get_notifications():
        rows=Notification.query.filter_by(user_id=current_user().id).order_by(Notification.created_at.desc()).all(); return jsonify({'ok':True,'items':[{'id':n.id,'message':n.message,'read':n.read,'product_id':n.product_id,'created_at':n.created_at.isoformat()} for n in rows],'unread':sum(not n.read for n in rows)})
    @app.post('/api/notifications/<int:nid>/read')
    @login_required
    def read_notification(nid):
        n=Notification.query.filter_by(id=nid,user_id=current_user().id).first_or_404(); n.read=True; db.session.commit(); return jsonify({'ok':True})
    @app.get('/notifications')
    @login_required
    def notification_page(): return render_template('notifications.html')
    @app.route('/checkout',methods=['GET','POST'])
    @login_required
    def checkout():
        if request.method=='POST':
            d=request.get_json(silent=True) or {}; u=current_user()
            if d.get('payment_method')=='online': return api_error('Online payment is currently disabled in this demonstration project. No money will be charged.',400)
            if d.get('payment_method')!='cod': return api_error('Choose Cash on Delivery. Online payment is disabled.',400)
            if len(d.get('address','').strip())<8 or len(d.get('phone','').strip())<7: return api_error('Enter a valid delivery address and contact number.',400)
            try:
                rows=CartItem.query.filter_by(user_id=u.id).with_for_update().all()
                if not rows: return api_error('Your cart is empty.',400)
                subtotal=Decimal('0.00')
                for i in rows:
                    if not i.product.active or i.quantity>i.product.stock: return api_error(f'{i.product.name} is no longer available in the requested quantity.',409)
                    subtotal+=i.product.final_price*i.quantity
                order=Order(user_id=u.id,address=d['address'].strip(),phone=d['phone'].strip(),subtotal=subtotal,discount=Decimal('0'),delivery_fee=Decimal('0'),total=subtotal,payment_method='Cash on Delivery',payment_status='Not Paid',status='Pending')
                db.session.add(order); db.session.flush()
                for i in rows:
                    p=i.product; price=p.final_price; order.items.append(OrderItem(product_id=p.id,product_name=p.name,unit_price=price,quantity=i.quantity,item_subtotal=price*i.quantity)); p.stock-=i.quantity; db.session.delete(i)
                db.session.commit(); return jsonify({'ok':True,'order_id':order.id}),201
            except Exception:
                db.session.rollback(); app.logger.exception('Order creation failed'); return api_error('We could not place the order. Please try again.',500)
        return render_template('checkout.html')
    @app.get('/orders')
    @login_required
    def orders_page(): return render_template('orders.html')
    @app.get('/api/orders')
    @login_required
    def my_orders():
        rows=Order.query.filter_by(user_id=current_user().id).order_by(Order.created_at.desc()).all(); return jsonify({'ok':True,'items':[{'id':o.id,'created_at':o.created_at.isoformat(),'total':str(o.total),'status':o.status,'payment_status':o.payment_status,'items':[{'name':i.product_name,'quantity':i.quantity,'unit_price':str(i.unit_price),'subtotal':str(i.item_subtotal)} for i in o.items]} for o in rows]})
    @app.get('/orders/<int:oid>')
    @login_required
    def order_page(oid):
        o=Order.query.filter_by(id=oid,user_id=current_user().id).first_or_404(); return render_template('order_detail.html',order=o)
    @app.get('/account')
    @login_required
    def account(): return render_template('account.html')
    @app.get('/admin')
    @admin_required
    def admin(): return render_template('admin.html')
    @app.get('/admin/products/<int:pid>/edit')
    @admin_required
    def admin_product_edit_page(pid):
        if not db.session.get(Product,pid): abort(404)
        return render_template('admin_product_edit.html',product_id=pid)
    @app.get('/api/admin/stats')
    @admin_required
    def admin_stats():
        return jsonify({'ok':True,'customers':User.query.filter_by(role='customer').count(),'products':Product.query.filter_by(active=True).count(),'available':Product.query.filter(Product.active.is_(True),Product.stock>0).count(),'out_of_stock':Product.query.filter(Product.active.is_(True),Product.stock==0).count(),'orders':Order.query.count(),'pending':Order.query.filter_by(status='Pending').count(),'sales':str(db.session.query(func.coalesce(func.sum(Order.total),0)).filter(Order.payment_status!='Not Paid',Order.status!='Cancelled').scalar())})
    @app.get('/api/admin/products')
    @admin_required
    def admin_products():
        query=Product.query.join(Category)
        term=request.args.get('q','').strip()
        if term:
            like=f'%{term}%'
            query=query.filter(or_(Product.name.ilike(like),Product.brand.ilike(like),Category.name.ilike(like)))
        return jsonify({'ok':True,'items':[product_json(p) for p in query.order_by(Product.name).all()]})
    @app.get('/api/admin/products/<int:pid>')
    @admin_required
    def admin_product_detail(pid):
        p=db.session.get(Product,pid)
        return jsonify({'ok':True,'item':product_json(p)}) if p else api_error('Product not found.',404)
    @app.post('/api/admin/products')
    @admin_required
    def admin_product_create(): return save_product()
    @app.put('/api/admin/products/<int:pid>')
    @admin_required
    def admin_product_update(pid): return save_product(pid)
    def save_product(pid=None):
        d=request.get_json(silent=True) or {}; p=db.session.get(Product,pid) if pid else Product()
        old_stock=p.stock if pid and p else 0
        try:
            p.name=d['name'].strip(); p.description=d.get('description',''); p.brand=d.get('brand',''); p.price=Decimal(str(d['price'])); p.discount_percent=Decimal(str(d.get('discount_percent',0))); p.stock=int(d.get('stock',0)); p.pack_size=d.get('pack_size',''); p.image_url=d.get('image_url',''); p.featured=bool(d.get('featured',False)); p.active=bool(d.get('active',True)); p.category_id=int(d['category_id'])
            if p.price<=0 or p.discount_percent<0 or p.discount_percent>100 or p.stock<0: raise ValueError()
            if not db.session.get(Category,p.category_id): raise ValueError()
        except (KeyError,ValueError,TypeError,ArithmeticError): return api_error('Please provide valid product fields, category, price, discount, and stock.',400)
        db.session.add(p); db.session.flush()
        if old_stock==0 and p.stock>0:
            event=f'{p.id}:{datetime.utcnow().isoformat()}'
            subs=WishlistItem.query.filter_by(product_id=p.id).all()
            for s in subs: db.session.add(Notification(user_id=s.user_id,product_id=p.id,message=f'{p.name} is back in stock.',event_key=f'{event}:{s.user_id}'))
        db.session.commit(); return jsonify({'ok':True,'item':product_json(p)}),201 if not pid else 200
    @app.delete('/api/admin/products/<int:pid>')
    @admin_required
    def admin_product_deactivate(pid):
        p=db.session.get(Product,pid)
        if not p: return api_error('Product not found.',404)
        p.active=False; db.session.commit(); return jsonify({'ok':True})
    @app.get('/api/admin/orders')
    @admin_required
    def admin_orders():
        rows=Order.query.order_by(Order.created_at.desc()).all(); return jsonify({'ok':True,'items':[{'id':o.id,'customer':o.user.name,'email':o.user.email,'created_at':o.created_at.isoformat(),'total':str(o.total),'status':o.status,'payment_status':o.payment_status} for o in rows]})
    @app.patch('/api/admin/orders/<int:oid>')
    @admin_required
    def admin_order_update(oid):
        o=db.session.get(Order,oid); status=(request.get_json(silent=True) or {}).get('status'); allowed={'Pending','Confirmed','Processing','Shipped','Delivered','Cancelled'}
        if not o: return api_error('Order not found.',404)
        if status not in allowed: return api_error('Invalid order status.',400)
        if o.status in ('Delivered','Cancelled') and status!=o.status: return api_error('This order is in a final state.',409)
        o.status=status; db.session.commit(); return jsonify({'ok':True})
    @app.get('/api/admin/customers')
    @admin_required
    def admin_customers(): return jsonify({'ok':True,'items':[{'id':u.id,'name':u.name,'email':u.email,'phone':u.phone,'created_at':u.created_at.isoformat()} for u in User.query.filter_by(role='customer').order_by(User.created_at.desc()).all()]})
    @app.errorhandler(404)
    def not_found(e): return render_template('error.html',code=404,message='The page or item was not found.'),404
    @app.errorhandler(403)
    def forbidden(e): return render_template('error.html',code=403,message='You do not have permission to view this page.'),403
    return app

app=create_app()
if __name__=='__main__': app.run(debug=os.getenv('FLASK_DEBUG','0')=='1')
