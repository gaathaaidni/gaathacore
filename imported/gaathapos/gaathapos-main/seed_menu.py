"""Seed sample menu items into the database"""
from app import create_app
from extensions import db
from models import MenuItem

SAMPLE_ITEMS = [
    # Appetizers
    {"name": "Bruschetta", "description": "Toasted bread with tomato and basil", "price": 8.50, "available": True},
    {"name": "Calamari Fritti", "description": "Fried squid with marinara sauce", "price": 12.00, "available": True},
    {"name": "Mozzarella Sticks", "description": "Breaded mozzarella with marinara", "price": 9.99, "available": True},
    
    # Salads
    {"name": "Caesar Salad", "description": "Romaine, parmesan, croutons, caesar dressing", "price": 11.50, "available": True},
    {"name": "Greek Salad", "description": "Feta, olives, tomatoes, cucumbers, olive oil", "price": 10.99, "available": True},
    {"name": "Caprese Salad", "description": "Mozzarella, tomatoes, basil, balsamic vinegar", "price": 12.50, "available": True},
    
    # Pasta
    {"name": "Spaghetti Carbonara", "description": "Pasta with eggs, bacon, parmesan", "price": 14.99, "available": True},
    {"name": "Fettuccine Alfredo", "description": "Pasta with creamy parmesan sauce", "price": 13.99, "available": True},
    {"name": "Penne Arrabbiata", "description": "Spicy tomato sauce with garlic", "price": 12.99, "available": True},
    {"name": "Lasagna", "description": "Layers of pasta, meat sauce, and cheese", "price": 15.50, "available": True},
    
    # Pizzas
    {"name": "Margherita Pizza", "description": "Tomato, mozzarella, basil, olive oil", "price": 14.50, "available": True},
    {"name": "Pepperoni Pizza", "description": "Tomato sauce, mozzarella, pepperoni", "price": 15.99, "available": True},
    {"name": "Quattro Formaggi Pizza", "description": "Four cheese blend", "price": 16.99, "available": True},
    {"name": "Vegetarian Pizza", "description": "Mixed vegetables on tomato sauce", "price": 14.99, "available": True},
    
    # Main Courses
    {"name": "Grilled Salmon", "description": "Fresh salmon with lemon and herbs", "price": 22.99, "available": True},
    {"name": "Chicken Parmesan", "description": "Breaded chicken with marinara and cheese", "price": 18.50, "available": True},
    {"name": "Ribeye Steak", "description": "12oz premium cut with garlic butter", "price": 28.99, "available": True},
    
    # Desserts
    {"name": "Tiramisu", "description": "Italian mascarpone dessert with espresso", "price": 7.99, "available": True},
    {"name": "Panna Cotta", "description": "Creamy vanilla with berry coulis", "price": 8.50, "available": True},
    {"name": "Chocolate Lava Cake", "description": "Warm chocolate cake with molten center", "price": 9.99, "available": True},
    
    # Beverages
    {"name": "Espresso", "description": "Single shot of premium espresso", "price": 2.50, "available": True},
    {"name": "Cappuccino", "description": "Espresso with steamed milk and foam", "price": 4.50, "available": True},
    {"name": "Italian Soda", "description": "Sparkling water with fruit syrup", "price": 3.99, "available": True},
    {"name": "Wine Glass", "description": "Selection of red or white wines", "price": 7.00, "available": True},
]

def seed_menu():
    """Add sample menu items to the database"""
    app = create_app()
    
    with app.app_context():
        # Check if menu items already exist
        existing_count = MenuItem.query.count()
        
        if existing_count > 0:
            print(f"✓ Database already has {existing_count} menu items. Skipping seed.")
            return
        
        print("Seeding sample menu items...")
        
        for item_data in SAMPLE_ITEMS:
            item = MenuItem(
                name=item_data["name"],
                description=item_data["description"],
                price=item_data["price"],
                available=item_data["available"]
            )
            db.session.add(item)
        
        db.session.commit()
        print(f"✓ Successfully seeded {len(SAMPLE_ITEMS)} menu items")

if __name__ == "__main__":
    seed_menu()
