"""Create the ten categories and an idempotent 50-item sample grocery catalog."""
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app, db, Category, Product

categories = [
    'Fruits', 'Vegetables', 'Dairy and Eggs', 'Rice and Grains',
    'Pulses and Lentils', 'Snacks', 'Beverages', 'Bakery',
    'Personal Care', 'Household Essentials',
]

# name, category, brand, description, pack size, price, discount, image URL, stock
# Five products are included in each category. Red Tomatoes starts out of stock
# so the wishlist/back-in-stock notification workflow can be demonstrated.
products = [
    ('Alphonso Mango', 'Fruits', 'FreshFarm', 'Naturally sweet seasonal mangoes.', '1 kg', '199.00', 10, 'https://images.unsplash.com/photo-1553279768-865429fa0078?auto=format&fit=crop&w=700&q=80', 40),
    ('Robusta Bananas', 'Fruits', 'FreshFarm', 'Fresh ripe bananas, perfect for breakfast and snacks.', '1 dozen', '59.00', 0, 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=700&q=80', 35),
    ('Shimla Apples', 'Fruits', 'Himachal Fresh', 'Crisp apples with a naturally sweet flavor.', '1 kg', '169.00', 5, 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?auto=format&fit=crop&w=700&q=80', 28),
    ('Nagpur Oranges', 'Fruits', 'Citrus Valley', 'Juicy oranges rich in refreshing citrus flavor.', '1 kg', '89.00', 0, 'https://images.unsplash.com/photo-1547514701-42782101795e?auto=format&fit=crop&w=700&q=80', 30),
    ('Green Grapes', 'Fruits', 'FreshFarm', 'Seedless green grapes, washed and ready to enjoy.', '500 g', '75.00', 0, 'https://images.unsplash.com/photo-1537640538966-79f369143f8f?auto=format&fit=crop&w=700&q=80', 24),

    ('Red Tomatoes', 'Vegetables', 'Farm Fresh', 'Juicy ripe tomatoes for everyday cooking.', '500 g', '35.00', 0, 'https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=700&q=80', 0),
    ('Fresh Potatoes', 'Vegetables', 'Farm Fresh', 'Versatile, clean potatoes for curries and sides.', '1 kg', '38.00', 0, 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?auto=format&fit=crop&w=700&q=80', 50),
    ('Red Onions', 'Vegetables', 'Farm Fresh', 'Everyday red onions with a balanced flavor.', '1 kg', '42.00', 0, 'https://images.unsplash.com/photo-1508747703725-719777637510?auto=format&fit=crop&w=700&q=80', 45),
    ('Baby Spinach', 'Vegetables', 'Green Basket', 'Tender spinach leaves, carefully cleaned and packed.', '250 g', '32.00', 0, 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&w=700&q=80', 18),
    ('Cauliflower', 'Vegetables', 'Farm Fresh', 'Fresh whole cauliflower for everyday recipes.', '1 pc', '42.00', 0, 'https://images.unsplash.com/photo-1568584711271-6c929fb49c0b?auto=format&fit=crop&w=700&q=80', 16),

    ('Whole Milk', 'Dairy and Eggs', 'Amul', 'Fresh pasteurized toned milk.', '1 L', '68.00', 0, 'https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=700&q=80', 40),
    ('Farm Eggs', 'Dairy and Eggs', 'Happy Hen', 'Protein-rich farm fresh eggs.', '6 pcs', '55.00', 0, 'https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=700&q=80', 32),
    ('Fresh Paneer', 'Dairy and Eggs', 'Amul', 'Soft cottage cheese for curries, wraps, and grilling.', '200 g', '92.00', 0, 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=700&q=80', 20),
    ('Plain Curd', 'Dairy and Eggs', 'Mother Dairy', 'Smooth set curd made from fresh milk.', '400 g', '40.00', 0, 'https://images.unsplash.com/photo-1571212515416-fef01fc43637?auto=format&fit=crop&w=700&q=80', 26),
    ('Salted Butter', 'Dairy and Eggs', 'Amul', 'Creamy salted butter for toast and cooking.', '100 g', '58.00', 0, 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?auto=format&fit=crop&w=700&q=80', 25),

    ('Basmati Rice', 'Rice and Grains', 'India Gate', 'Aromatic long grain basmati rice.', '1 kg', '145.00', 5, 'https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=700&q=80', 40),
    ('Brown Rice', 'Rice and Grains', 'Daawat', 'Nutty wholegrain brown rice for everyday meals.', '1 kg', '125.00', 0, 'https://images.unsplash.com/photo-1516684732162-798a0062be99?auto=format&fit=crop&w=700&q=80', 30),
    ('Whole Wheat Atta', 'Rice and Grains', 'Aashirvaad', 'Stone-ground whole wheat flour for soft rotis.', '5 kg', '285.00', 5, 'https://images.unsplash.com/photo-1627485937980-221c88ac04f9?auto=format&fit=crop&w=700&q=80', 24),
    ('Rolled Oats', 'Rice and Grains', 'Quaker', 'Wholegrain rolled oats for breakfast and baking.', '1 kg', '189.00', 0, 'https://images.unsplash.com/photo-1517673132405-a56a62b18caf?auto=format&fit=crop&w=700&q=80', 22),
    ('Thick Poha', 'Rice and Grains', 'Tata Sampann', 'Flattened rice flakes for a quick savory breakfast.', '500 g', '52.00', 0, 'https://images.unsplash.com/photo-1517673132405-a56a62b18caf?auto=format&fit=crop&w=700&q=80', 28),

    ('Toor Dal', 'Pulses and Lentils', 'Tata Sampann', 'Unpolished split pigeon peas.', '1 kg', '165.00', 0, 'https://images.unsplash.com/photo-1515543904379-3d757afe72e4?auto=format&fit=crop&w=700&q=80', 30),
    ('Moong Dal', 'Pulses and Lentils', 'Tata Sampann', 'Yellow split mung beans for dals and khichdi.', '1 kg', '138.00', 0, 'https://images.unsplash.com/photo-1515543904379-3d757afe72e4?auto=format&fit=crop&w=700&q=80', 25),
    ('Kabuli Chana', 'Pulses and Lentils', 'Tata Sampann', 'Premium chickpeas for chole and salads.', '1 kg', '145.00', 0, 'https://images.unsplash.com/photo-1515543904379-3d757afe72e4?auto=format&fit=crop&w=700&q=80', 26),
    ('Red Kidney Beans', 'Pulses and Lentils', 'Tata Sampann', 'Whole rajma beans for homestyle curries.', '500 g', '92.00', 0, 'https://images.unsplash.com/photo-1515543904379-3d757afe72e4?auto=format&fit=crop&w=700&q=80', 20),
    ('Masoor Dal', 'Pulses and Lentils', 'Tata Sampann', 'Quick-cooking red lentils with a mild flavor.', '1 kg', '128.00', 0, 'https://images.unsplash.com/photo-1515543904379-3d757afe72e4?auto=format&fit=crop&w=700&q=80', 30),

    ('Masala Oats', 'Snacks', 'Saffola', 'Savory wholegrain oats with spices.', '400 g', '99.00', 0, 'https://images.unsplash.com/photo-1517673132405-a56a62b18caf?auto=format&fit=crop&w=700&q=80', 24),
    ('Classic Potato Chips', 'Snacks', ' lays', 'Crispy salted potato chips for sharing.', '50 g', '20.00', 0, 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?auto=format&fit=crop&w=700&q=80', 60),
    ('Butter Cookies', 'Snacks', 'Britannia', 'Golden crunchy butter cookies for tea time.', '200 g', '45.00', 0, 'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&w=700&q=80', 34),
    ('Roasted Peanuts', 'Snacks', 'Haldiram', 'Crunchy roasted peanuts with a light salt seasoning.', '200 g', '48.00', 0, 'https://images.unsplash.com/photo-1567892737950-30c4db37cd89?auto=format&fit=crop&w=700&q=80', 28),
    ('Roasted Makhana', 'Snacks', 'Farmley', 'Light roasted fox nuts for a satisfying snack.', '100 g', '115.00', 0, 'https://images.unsplash.com/photo-1599599810694-b5ac4dd5a084?auto=format&fit=crop&w=700&q=80', 18),

    ('Orange Juice', 'Beverages', 'Real', 'Refreshing fruit juice drink.', '1 L', '120.00', 0, 'https://images.unsplash.com/photo-1600271886742-f049cd451bba?auto=format&fit=crop&w=700&q=80', 28),
    ('Assam Tea', 'Beverages', 'Tata Tea', 'Strong Assam tea leaves for a full-bodied cup.', '250 g', '145.00', 0, 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=700&q=80', 32),
    ('Instant Coffee', 'Beverages', 'Nescafé', 'Rich instant coffee for a quick cup.', '100 g', '285.00', 0, 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?auto=format&fit=crop&w=700&q=80', 20),
    ('Coconut Water', 'Beverages', 'Raw Pressery', 'Chilled-ready tender coconut water.', '200 ml', '45.00', 0, 'https://images.unsplash.com/photo-1553909489-cd47e0ef937f?auto=format&fit=crop&w=700&q=80', 25),
    ('Green Tea', 'Beverages', 'Tetley', 'Light green tea bags for a gentle daily brew.', '25 bags', '135.00', 0, 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?auto=format&fit=crop&w=700&q=80', 18),

    ('Whole Wheat Bread', 'Bakery', 'Modern', 'Soft whole wheat sandwich bread.', '400 g', '48.00', 0, 'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=700&q=80', 20),
    ('Burger Buns', 'Bakery', 'English Oven', 'Soft sesame burger buns, ready to fill.', '4 pcs', '42.00', 0, 'https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=700&q=80', 16),
    ('Milk Rusk', 'Bakery', 'Britannia', 'Crunchy baked rusk for tea and coffee.', '200 g', '38.00', 0, 'https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=700&q=80', 22),
    ('Pav Buns', 'Bakery', 'Modern', 'Soft dinner rolls for pav bhaji and snacks.', '6 pcs', '35.00', 0, 'https://images.unsplash.com/photo-1555507036-ab1f4038808a?auto=format&fit=crop&w=700&q=80', 15),
    ('Chocolate Muffins', 'Bakery', 'Theobroma', 'Moist chocolate muffins baked for a sweet treat.', '2 pcs', '89.00', 0, 'https://images.unsplash.com/photo-1607958996333-41aef7caefaa?auto=format&fit=crop&w=700&q=80', 12),

    ('Gentle Hand Wash', 'Personal Care', 'Dove', 'Moisturizing hand wash for everyday use.', '250 ml', '89.00', 0, 'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=700&q=80', 22),
    ('Daily Shampoo', 'Personal Care', 'Dove', 'Nourishing shampoo for soft, clean hair.', '340 ml', '210.00', 0, 'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=700&q=80', 18),
    ('Moisturizing Soap', 'Personal Care', 'Dove', 'Gentle cleansing bar with a moisturizing feel.', '3 x 100 g', '145.00', 0, 'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=700&q=80', 26),
    ('Mint Toothpaste', 'Personal Care', 'Colgate', 'Fresh mint toothpaste for daily oral care.', '150 g', '78.00', 0, 'https://images.unsplash.com/photo-1609840114035-3c981b782dfe?auto=format&fit=crop&w=700&q=80', 30),
    ('Face Wash', 'Personal Care', 'Himalaya', 'Gentle face wash for a fresh everyday cleanse.', '100 ml', '110.00', 0, 'https://images.unsplash.com/photo-1608248543803-ba4f8c70ae0b?auto=format&fit=crop&w=700&q=80', 16),

    ('Dishwashing Liquid', 'Household Essentials', 'Pril', 'Grease-cutting dishwashing liquid.', '500 ml', '95.00', 0, 'https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=700&q=80', 24),
    ('Laundry Detergent', 'Household Essentials', 'Surf Excel', 'Effective detergent powder for everyday laundry.', '1 kg', '145.00', 0, 'https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=700&q=80', 20),
    ('Floor Cleaner', 'Household Essentials', 'Lizol', 'Fresh-scented cleaner for hard floors.', '500 ml', '112.00', 0, 'https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=700&q=80', 18),
    ('Kitchen Garbage Bags', 'Household Essentials', 'Solimo', 'Strong drawstring bags for everyday kitchen waste.', '30 bags', '99.00', 0, 'https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=700&q=80', 25),
    ('Paper Tissue Rolls', 'Household Essentials', 'Origami', 'Soft absorbent tissue rolls for home use.', '4 rolls', '115.00', 0, 'https://images.unsplash.com/photo-1585421514738-01798e348b17?auto=format&fit=crop&w=700&q=80', 20),
]

with app.app_context():
    db.create_all()
    cats = {}
    for name in categories:
        category = Category.query.filter_by(name=name).first()
        if not category:
            slug = name.lower().replace(' ', '-')
            category = Category(name=name, slug=slug)
            db.session.add(category)
        cats[name] = category
    db.session.flush()

    added = 0
    for name, category, brand, description, pack, price, discount, image, stock in products:
        if Product.query.filter_by(name=name).first():
            continue
        db.session.add(Product(
            name=name, category_id=cats[category].id, brand=brand.strip(),
            description=description, pack_size=pack, price=Decimal(price),
            discount_percent=Decimal(str(discount)), stock=stock,
            image_url=image, featured=True,
        ))
        added += 1
    db.session.commit()
    print(f"Catalog seed complete: {len(products)} sample products across {len(categories)} categories ({added} newly added).")
