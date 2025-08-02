from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
import json, os, time
from werkzeug.utils import secure_filename
import math
import re
from dotenv import load_dotenv
import paypalrestsdk

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'qualclamps_secret')

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": os.getenv('PAYPAL_MODE', 'sandbox'),  # sandbox or live
    "client_id": os.getenv('PAYPAL_CLIENT_ID'),
    "client_secret": os.getenv('PAYPAL_CLIENT_SECRET')
})

# Configure email settings
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'postman@qualclamps.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'postman@qualclamps.com')

# Initialize Mail
mail = Mail(app)

# Configure file upload settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.config['UPLOAD_EXTENSIONS'] = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.avif', '.jxl'}

# Ensure upload and data directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join('data'), exist_ok=True)

# Configure session settings
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours (1 day)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Add slugify function to Jinja2 global functions
def slugify(text):
    """Convert text to URL-friendly slug"""
    text = str(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

# File upload helper functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in app.config['UPLOAD_EXTENSIONS']

def save_uploaded_file(file, filename=None):
    """Save uploaded file with proper error handling and verification"""
    try:
        if not file:
            return None, "No file object provided"
            
        if not file.filename:
            return None, "No filename provided"
        
        print(f"[UPLOAD] Starting upload for: {file.filename}")
        
        # Check file extension
        if not allowed_file(file.filename):
            allowed_exts = ', '.join(app.config['UPLOAD_EXTENSIONS'])
            return None, f"File type not allowed. Allowed types: {allowed_exts}"
        
        # Use provided filename or secure the original filename
        if filename:
            secure_name = filename
        else:
            secure_name = secure_filename(file.filename)
        
        if not secure_name:
            return None, "Invalid filename after security check"
        
        # Add timestamp to avoid naming conflicts
        timestamp = str(int(time.time()))
        name_parts = secure_name.rsplit('.', 1)
        if len(name_parts) == 2:
            secure_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            secure_name = f"{secure_name}_{timestamp}"
        
        # Ensure upload directory exists
        upload_dir = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            print(f"[UPLOAD] Created upload directory: {upload_dir}")
        
        # Save file
        file_path = os.path.join(upload_dir, secure_name)
        print(f"[UPLOAD] Saving to: {file_path}")
        
        # Save the file
        file.save(file_path)
        
        # Verify file was saved and has content
        if not os.path.exists(file_path):
            return None, f"File was not saved to {file_path}"
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            try:
                os.remove(file_path)
            except:
                pass
            return None, "Uploaded file is empty"
        
        print(f"[UPLOAD] File saved successfully: {secure_name} ({file_size} bytes)")
        return secure_name, None
        
    except Exception as e:
        error_msg = f"Error saving file: {str(e)}"
        print(f"[UPLOAD ERROR] {error_msg}")
        return None, error_msg

# Make slugify available in templates
app.jinja_env.globals.update(slugify=slugify)
app.jinja_env.filters['slugify'] = slugify

# Shipping configuration
EXCLUDED_COUNTRIES = ['Pakistan', 'China']
SHIPPING_RATE_PER_1000KM_PER_KG = 14  # Updated rate per 1000km per kg
SHIPPING_DISCOUNT = 0.50  # Increased from 30% to 50% discount on calculated shipping

# Approximate distances from India (Faridabad) to major countries/regions in kilometers
COUNTRY_DISTANCES = {
    'india': 0,  # Domestic shipping
    'myanmar': 2000,
    'thailand': 3000,
    'malaysia': 4000,
    'singapore': 4200,
    'indonesia': 4500,
    'philippines': 5000,
    'vietnam': 3500,
    'cambodia': 3800,
    'laos': 3200,
    'japan': 6000,
    'south korea': 5500,
    'mongolia': 4000,
    'kazakhstan': 2500,
    'uzbekistan': 2000,
    'turkmenistan': 1800,
    'kyrgyzstan': 2200,
    'tajikistan': 1800,
    'iran': 1500,
    'iraq': 2200,
    'syria': 3000,
    'turkey': 3500,
    'georgia': 3200,
    'armenia': 3000,
    'azerbaijan': 2800,
    'saudi arabia': 2500,
    'united arab emirates': 2000,
    'qatar': 2200,
    'kuwait': 2300,
    'bahrain': 2200,
    'oman': 2000,
    'yemen': 2800,
    'jordan': 3200,
    'lebanon': 3300,
    'israel': 3400,
    'egypt': 3800,
    'libya': 4500,
    'tunisia': 5000,
    'algeria': 5200,
    'morocco': 5800,
    'sudan': 4000,
    'ethiopia': 4200,
    'somalia': 3800,
    'kenya': 4500,
    'uganda': 4800,
    'tanzania': 5000,
    'south africa': 7000,
    'nigeria': 6000,
    'ghana': 6500,
    'ivory coast': 6800,
    'senegal': 7200,
    'mali': 6800,
    'burkina faso': 6500,
    'niger': 6200,
    'chad': 5800,
    'cameroon': 5800,
    'central african republic': 5500,
    'democratic republic of congo': 6000,
    'angola': 6800,
    'zambia': 6200,
    'zimbabwe': 6500,
    'botswana': 6800,
    'namibia': 7200,
    'madagascar': 5500,
    'mauritius': 4800,
    'russia': 3500,
    'belarus': 4500,
    'poland': 5000,
    'germany': 5500,
    'france': 6000,
    'spain': 6500,
    'portugal': 7000,
    'italy': 5200,
    'switzerland': 5600,
    'austria': 5400,
    'czech republic': 5200,
    'slovakia': 5100,
    'hungary': 5000,
    'romania': 4800,
    'bulgaria': 4600,
    'greece': 4800,
    'albania': 5000,
    'serbia': 4900,
    'croatia': 5200,
    'slovenia': 5400,
    'bosnia and herzegovina': 5100,
    'montenegro': 5000,
    'north macedonia': 4900,
    'moldova': 4600,
    'lithuania': 4800,
    'latvia': 4900,
    'estonia': 5000,
    'finland': 5500,
    'sweden': 5800,
    'norway': 6000,
    'denmark': 5600,
    'netherlands': 5800,
    'belgium': 5900,
    'luxembourg': 5800,
    'united kingdom': 6200,
    'ireland': 6500,
    'iceland': 7000,
    'united states': 12000,
    'canada': 11500,
    'mexico': 15000,
    'guatemala': 16000,
    'belize': 16200,
    'honduras': 16100,
    'el salvador': 16000,
    'nicaragua': 16300,
    'costa rica': 16500,
    'panama': 16800,
    'colombia': 17000,
    'venezuela': 17200,
    'guyana': 17500,
    'suriname': 17600,
    'brazil': 15000,
    'ecuador': 17500,
    'peru': 17000,
    'bolivia': 16500,
    'paraguay': 15800,
    'uruguay': 15500,
    'argentina': 15200,
    'chile': 16000,
    'australia': 8000,
    'new zealand': 9500,
    'papua new guinea': 7500,
    'fiji': 9000,
    'solomon islands': 8500,
    'vanuatu': 8800,
    'new caledonia': 8600,
    'samoa': 10000,
    'tonga': 10200,
    'cook islands': 11000,
    'french polynesia': 12000
}

def is_shipping_allowed(country):
    """Check if shipping is allowed to a specific country"""
    return country.lower() not in [c.lower() for c in EXCLUDED_COUNTRIES]

def get_shipping_distance(country):
    """Get shipping distance to a country"""
    country_key = country.lower().strip()
    return COUNTRY_DISTANCES.get(country_key, 10000)  # Default to 10000km if country not found

def calculate_shipping_cost(country, weight_kg, quantity=1, method='air'):
    """Calculate shipping cost based on distance, weight, quantity, and shipping method"""
    if not is_shipping_allowed(country):
        return None
    
    # Round up weight to minimum 1kg
    shipping_weight = math.ceil(weight_kg) if weight_kg > 0 else 1
    
    # Special case for India - $2.50 per kg base rate (reduced from $4.50)
    if country.lower() == 'india':
        base_cost = 5.8 * shipping_weight
    else:
        # Get distance for other countries
        distance_km = get_shipping_distance(country)
        
        # Calculate base air shipping cost: $14 per 1000km per kg, then apply 50% discount
        base_cost = (distance_km / 1000) * shipping_weight * SHIPPING_RATE_PER_1000KM_PER_KG
        base_cost = base_cost * (1 - SHIPPING_DISCOUNT)
    
    # Apply quantity-based discounts for air shipping
    if method == 'air':
        quantity_discount = 0.0
        if quantity >= 5000:
            quantity_discount = 0.92  # 92% discount for 5000+ pieces
        elif quantity >= 3000:
            quantity_discount = 0.91  # 91% discount for 3000+ pieces
        elif quantity >= 2000:
            quantity_discount = 0.90  # 90% discount for 2000+ pieces
        elif quantity >= 1500:
            quantity_discount = 0.89  # 89% discount for 1500+ pieces
        elif quantity >= 1000:
            quantity_discount = 0.88  # 88% discount for 1000+ pieces
        elif quantity >= 500:
            quantity_discount = 0.29  # 29% discount for 500+ pieces
        elif quantity >= 200:
            quantity_discount = 0.18  # 18% discount for 200+ pieces
        elif quantity >= 100:
            quantity_discount = 0.14  # 14% discount for 100+ pieces
        elif quantity >= 50:
            quantity_discount = 0.08  # 8% discount for 50+ pieces
        
        final_cost = base_cost * (1 - quantity_discount)
    elif method == 'sea':
        # Sea shipping is 16% of the FINAL air shipping cost (including quantity discounts)
        # First calculate what air shipping would cost with discounts
        quantity_discount = 0.0
        if quantity >= 5000:
            quantity_discount = 0.92  # 92% discount for 5000+ pieces
        elif quantity >= 3000:
            quantity_discount = 0.91  # 91% discount for 3000+ pieces
        elif quantity >= 2000:
            quantity_discount = 0.90  # 90% discount for 2000+ pieces
        elif quantity >= 1500:
            quantity_discount = 0.89  # 89% discount for 1500+ pieces
        elif quantity >= 1000:
            quantity_discount = 0.88  # 88% discount for 1000+ pieces
        elif quantity >= 500:
            quantity_discount = 0.29  # 29% discount for 500+ pieces
        elif quantity >= 200:
            quantity_discount = 0.18  # 18% discount for 200+ pieces
        elif quantity >= 100:
            quantity_discount = 0.14  # 14% discount for 100+ pieces
        elif quantity >= 50:
            quantity_discount = 0.08  # 8% discount for 50+ pieces
        
        air_cost_with_discounts = base_cost * (1 - quantity_discount)
        base_sea_cost = air_cost_with_discounts * 0.16  # 16% of final air cost
        
        # Apply additional quantity-based differential discounts to sea shipping
        sea_additional_discount = 0.0
        if quantity >= 5000:
            sea_additional_discount = 0.320  # Additional 32% discount for 5000+ pieces
        elif quantity >= 3000:
            sea_additional_discount = 0.28  # Additional 28% discount for 3000+ pieces
        elif quantity >= 2000:
            sea_additional_discount = 0.25  # Additional 25% discount for 2000+ pieces
        elif quantity >= 1500:
            sea_additional_discount = 0.22  # Additional 22% discount for 1500+ pieces
        elif quantity >= 1000:
            sea_additional_discount = 0.20  # Additional 20% discount for 1000+ pieces
        elif quantity >= 500:
            sea_additional_discount = 0.15  # Additional 15% discount for 500+ pieces
        elif quantity >= 200:
            sea_additional_discount = 0.10  # Additional 10% discount for 200+ pieces
        elif quantity >= 100:
            sea_additional_discount = 0.08  # Additional 8% discount for 100+ pieces
        elif quantity >= 50:
            sea_additional_discount = 0.05  # Additional 5% discount for 50+ pieces
        
        final_cost = base_sea_cost * (1 - sea_additional_discount)
    else:
        final_cost = base_cost
    
    return round(final_cost, 2)

def get_shipping_cost(country, weight_kg=1, quantity=1, method='air'):
    """Get shipping cost based on country, weight, quantity, and method (backward compatibility)"""
    return calculate_shipping_cost(country, weight_kg, quantity, method)

def get_cart_total_quantity():
    """Get total quantity of all items in cart"""
    cart = get_cart()
    total_quantity = 0
    for item in cart.values():
        total_quantity += item['quantity']
    return total_quantity

def should_auto_select_sea_shipping():
    """Check if sea shipping should be auto-selected based on quantity"""
    return get_cart_total_quantity() >= 1000

def create_paypal_payment(order_total, order_id, return_url, cancel_url):
    """Create a PayPal payment"""
    try:
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": return_url,
                "cancel_url": cancel_url
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"Quality Clamps Order #{order_id}",
                        "sku": order_id,
                        "price": f"{order_total:.2f}",
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": f"{order_total:.2f}",
                    "currency": "USD"
                },
                "description": f"Payment for Quality Clamps Order #{order_id}"
            }]
        })
        
        if payment.create():
            return payment
        else:
            print(f"PayPal payment creation error: {payment.error}")
            return None
    except Exception as e:
        print(f"PayPal payment creation exception: {e}")
        return None

def execute_paypal_payment(payment_id, payer_id):
    """Execute a PayPal payment after user approval"""
    try:
        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            return payment
        else:
            print(f"PayPal payment execution error: {payment.error}")
            return None
    except Exception as e:
        print(f"PayPal payment execution exception: {e}")
        return None

# Email helper functions
def send_order_notification(order_data):
    """Send order notification email to sales team"""
    try:
        # Create order summary
        order_items_html = ""
        for item in order_data['order_items']:
            order_items_html += f"""
            <tr>
                <td>{item['product']['name']}</td>
                <td>{item['quantity']}</td>
                <td>${item['final_unit_price']:.2f}</td>
                <td>${item['final_total']:.2f}</td>
            </tr>
            """
        
        # Create email content
        html_body = f"""
        <html>
        <body>
            <h2>New Order Received - {order_data['order_id']}</h2>
            
            <h3>Customer Information:</h3>
            <ul>
                <li><strong>Name:</strong> {order_data['customer_info']['name']}</li>
                <li><strong>Company:</strong> {order_data['customer_info'].get('company', 'N/A')}</li>
                <li><strong>Email:</strong> {order_data['customer_info']['email']}</li>
                <li><strong>Phone:</strong> {order_data['customer_info']['phone']}</li>
                <li><strong>Address:</strong> {order_data['customer_info']['address']}</li>
                <li><strong>City:</strong> {order_data['customer_info']['city']}</li>
                <li><strong>State:</strong> {order_data['customer_info']['state']}</li>
                <li><strong>Country:</strong> {order_data['customer_info']['country']}</li>
                <li><strong>Postal Code:</strong> {order_data['customer_info']['postal_code']}</li>
            </ul>
            
            <h3>Order Details:</h3>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr>
                    <th>Product</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                </tr>
                {order_items_html}
            </table>
            
            <h3>Order Summary:</h3>
            <ul>
                <li><strong>Subtotal:</strong> ${order_data['subtotal']:.2f}</li>
                <li><strong>Shipping ({order_data['customer_info']['shipping_method']}):</strong> ${order_data['shipping_cost']:.2f}</li>
                <li><strong>Total:</strong> ${order_data['total']:.2f}</li>
                <li><strong>Total Weight:</strong> {order_data['total_weight']:.2f} kg</li>
            </ul>
            
            <h3>Payment Information:</h3>
            <ul>
                <li><strong>Method:</strong> {order_data['payment_info']['method']}</li>
                <li><strong>Status:</strong> {order_data['payment_info']['status']}</li>
                <li><strong>Amount:</strong> ${order_data['payment_info']['amount']:.2f}</li>
            </ul>
            
            <h3>Additional Notes:</h3>
            <p>{order_data['customer_info'].get('notes', 'No additional notes')}</p>
            
            <p><strong>Order Date:</strong> {order_data.get('created_date', 'N/A')}</p>
        </body>
        </html>
        """
        
        # Send email
        msg = Message(
            subject=f'New Order: {order_data["order_id"]} - {order_data["customer_info"]["name"]}',
            recipients=['sales@qualclamps.com'],
            html=html_body,
            sender='postman@qualclamps.com'
        )
        
        mail.send(msg)
        print(f"Order notification email sent for {order_data['order_id']}")
        return True
        
    except Exception as e:
        print(f"Failed to send order notification email: {e}")
        return False

def send_contact_notification(contact_data):
    """Send contact form notification email to sales team"""
    try:
        # Create email content
        html_body = f"""
        <html>
        <body>
            <h2>New Contact Form Submission</h2>
            
            <h3>Contact Information:</h3>
            <ul>
                <li><strong>Name:</strong> {contact_data.get('name', 'N/A')}</li>
                <li><strong>Email:</strong> {contact_data.get('email', 'N/A')}</li>
                <li><strong>Phone:</strong> {contact_data.get('phone', 'N/A')}</li>
                <li><strong>Inquiry Type:</strong> {contact_data.get('inquiry', 'N/A')}</li>
            </ul>
            
            <h3>Message:</h3>
            <p>{contact_data.get('message', 'No message provided')}</p>
            
            <p><strong>Submitted on:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </body>
        </html>
        """
        
        # Send email
        msg = Message(
            subject=f'Contact Form: {contact_data.get("inquiry", "General")} - {contact_data.get("name", "Unknown")}',
            recipients=['sales@qualclamps.com'],
            html=html_body,
            sender='postman@qualclamps.com'
        )
        
        mail.send(msg)
        print(f"Contact form notification email sent for {contact_data.get('name', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"Failed to send contact notification email: {e}")
        return False

# Cart helper functions
def get_cart():
    """Get cart from session"""
    return session.get('cart', {})

def save_cart(cart):
    """Save cart to session"""
    session['cart'] = cart
    session.permanent = True  # Make cart persist across browser sessions

def add_to_cart(category_folder, product_slug, quantity=1, specifications=None, shipping=None):
    """Add item to cart"""
    cart = get_cart()
    
    # Create unique cart item key based on product and specifications
    spec_key = json.dumps(specifications or {}, sort_keys=True)
    cart_key = f"{category_folder}:{product_slug}:{spec_key}"
    
    if cart_key in cart:
        cart[cart_key]['quantity'] += quantity
        # Update shipping info if provided
        if shipping:
            cart[cart_key]['shipping'] = shipping
    else:
        cart[cart_key] = {
            'category_folder': category_folder,
            'product_slug': product_slug,
            'quantity': quantity,
            'specifications': specifications or {},
            'shipping': shipping or {},
            'added_at': time.time()
        }
    
    save_cart(cart)
    return cart_key

def remove_from_cart(cart_key):
    """Remove item from cart"""
    cart = get_cart()
    if cart_key in cart:
        del cart[cart_key]
        save_cart(cart)

def update_cart_quantity(cart_key, quantity):
    """Update quantity of cart item and recalculate shipping cost"""
    cart = get_cart()
    if cart_key in cart:
        if quantity <= 0:
            del cart[cart_key]
        else:
            cart[cart_key]['quantity'] = quantity
            
            # Recalculate shipping cost based on new quantity/weight
            item = cart[cart_key]
            if 'shipping' in item and item['shipping']:
                # Get product details to calculate new weight
                products = load_products(item['category_folder'])
                product = None
                for p in products:
                    if slugify(p['name']) == item['product_slug']:
                        product = p
                        break
                
                if product:
                    # Calculate new total weight for this item
                    unit_weight = float(product.get('weight', 0))
                    # Apply specification weight modifiers if any
                    for spec_category, selected_option in item['specifications'].items():
                        if 'specifications' in product:
                            for spec in product['specifications']:
                                if spec['category'] == spec_category:
                                    for option in spec['options']:
                                        if option['name'] == selected_option:
                                            unit_weight += float(option.get('weight_modifier', 0))
                                            break
                                    break
                    
                    new_total_weight = unit_weight * quantity
                    
                    # Get total cart quantity for shipping calculation
                    total_cart_quantity = get_cart_total_quantity()
                    
                    # Recalculate shipping cost with new weight and total quantity
                    country = item['shipping']['country']
                    method = item['shipping']['method']
                    new_shipping_cost = calculate_shipping_cost(country, new_total_weight, total_cart_quantity, method)
                    
                    # Update shipping cost in cart
                    if new_shipping_cost is not None:
                        cart[cart_key]['shipping']['cost'] = new_shipping_cost
        
        save_cart(cart)

def get_cart_total():
    """Calculate cart total with specifications, bulk discounts, and shipping"""
    cart = get_cart()
    total = 0.0
    
    for cart_key, item in cart.items():
        # Load product data
        products = load_products(item['category_folder'])
        product = None
        for p in products:
            if slugify(p['name']) == item['product_slug']:
                product = p
                break
        
        if product:
            # Calculate base price with specifications
            unit_price = float(product.get('price', 0))
            
            # Apply specification price modifiers
            for spec_category, selected_option in item['specifications'].items():
                if 'specifications' in product:
                    for spec in product['specifications']:
                        if spec['category'] == spec_category:
                            for option in spec['options']:
                                if option['name'] == selected_option:
                                    unit_price += float(option.get('price_modifier', 0))
                                    break
                            break
            
            # Apply bulk discount
            quantity = item['quantity']
            discount_rate = get_bulk_discount_rate(quantity)
            final_price = unit_price * (1 - discount_rate)
            
            # Add product total
            total += final_price * quantity
            
            # Add shipping cost if available
            shipping = item.get('shipping', {})
            if shipping and 'cost' in shipping:
                total += float(shipping['cost'])
    
    return round(total, 2)

def get_cart_products_total():
    """Calculate cart total for products only (excluding shipping)"""
    cart = get_cart()
    total = 0.0
    
    for cart_key, item in cart.items():
        # Load product data
        products = load_products(item['category_folder'])
        product = None
        for p in products:
            if slugify(p['name']) == item['product_slug']:
                product = p
                break
        
        if product:
            # Calculate base price with specifications
            unit_price = float(product.get('price', 0))
            
            # Apply specification price modifiers
            for spec_category, selected_option in item['specifications'].items():
                if 'specifications' in product:
                    for spec in product['specifications']:
                        if spec['category'] == spec_category:
                            for option in spec['options']:
                                if option['name'] == selected_option:
                                    unit_price += float(option.get('price_modifier', 0))
                                    break
                            break
            
            # Apply bulk discount
            quantity = item['quantity']
            discount_rate = get_bulk_discount_rate(quantity)
            final_price = unit_price * (1 - discount_rate)
            
            # Add product total only
            total += final_price * quantity
    
    return round(total, 2)

def get_cart_shipping_total():
    """Calculate total shipping cost for all cart items"""
    cart = get_cart()
    total = 0.0
    
    for cart_key, item in cart.items():
        shipping = item.get('shipping', {})
        if shipping and 'cost' in shipping:
            total += float(shipping['cost'])
    
    return round(total, 2)

def get_bulk_discount_rate(quantity):
    """Get bulk discount rate based on quantity"""
    if quantity >= 500:
        return 0.25  # 25%
    elif quantity >= 200:
        return 0.20  # 20%
    elif quantity >= 100:
        return 0.12  # 12%
    elif quantity >= 50:
        return 0.08  # 8%
    elif quantity >= 20:
        return 0.05  # 5%
    elif quantity >= 1:
        return 0.02  # 2%
    return 0.0

def get_cart_items_with_details():
    """Get cart items with full product details"""
    cart = get_cart()
    cart_items = []
    
    for cart_key, item in cart.items():
        # Load product data
        products = load_products(item['category_folder'])
        product = None
        for p in products:
            if slugify(p['name']) == item['product_slug']:
                product = p
                break
        
        if product:
            # Calculate price with specifications
            base_price = float(product.get('price', 0))
            unit_price = base_price
            total_spec_modifier = 0.0
            
            # Apply specification price modifiers
            spec_details = {}
            for spec_category, selected_option in item['specifications'].items():
                if 'specifications' in product:
                    for spec in product['specifications']:
                        if spec['category'] == spec_category:
                            for option in spec['options']:
                                if option['name'] == selected_option:
                                    modifier = float(option.get('price_modifier', 0))
                                    weight_modifier = float(option.get('weight_modifier', 0))
                                    unit_price += modifier
                                    total_spec_modifier += modifier
                                    spec_details[spec_category] = {
                                        'option': selected_option,
                                        'price_modifier': modifier,
                                        'weight_modifier': weight_modifier
                                    }
                                    break
                            break
            
            # Calculate totals with bulk discount
            quantity = item['quantity']
            discount_rate = get_bulk_discount_rate(quantity)
            discount_amount = unit_price * discount_rate
            final_unit_price = unit_price - discount_amount
            subtotal = unit_price * quantity
            total_discount = discount_amount * quantity
            final_total = final_unit_price * quantity
            
            # Calculate weight with modifiers
            base_weight = float(product.get('weight', 1.0))
            total_weight_modifier = 0.0
            for spec_category, selected_option in item['specifications'].items():
                if 'specifications' in product:
                    for spec in product['specifications']:
                        if spec['category'] == spec_category:
                            for option in spec['options']:
                                if option['name'] == selected_option:
                                    total_weight_modifier += float(option.get('weight_modifier', 0))
                                    break
                            break
            unit_weight = base_weight + total_weight_modifier
            total_weight = unit_weight * quantity
            
            # Recalculate shipping cost dynamically to ensure cart shows correct rates
            stored_shipping = item.get('shipping', {})
            shipping_info = stored_shipping.copy()  # Start with stored shipping info
            
            if stored_shipping and stored_shipping.get('country') and stored_shipping.get('method'):
                # Get total cart quantity for accurate shipping calculation
                total_cart_quantity = 0
                for cart_key_inner, item_inner in get_cart().items():
                    total_cart_quantity += item_inner['quantity']
                
                # Recalculate shipping cost with current quantity and method
                recalculated_cost = calculate_shipping_cost(
                    stored_shipping['country'], 
                    total_weight, 
                    total_cart_quantity, 
                    stored_shipping['method']
                )
                
                if recalculated_cost is not None:
                    shipping_info['cost'] = recalculated_cost
            
            cart_items.append({
                'cart_key': cart_key,
                'product': product,
                'category_folder': item['category_folder'],
                'quantity': quantity,
                'specifications': item['specifications'],
                'spec_details': spec_details,
                'shipping': shipping_info,
                'base_price': base_price,
                'total_spec_modifier': total_spec_modifier,
                'unit_price': unit_price,
                'base_weight': base_weight,
                'total_weight_modifier': total_weight_modifier,
                'unit_weight': unit_weight,
                'total_weight': total_weight,
                'discount_rate': discount_rate,
                'discount_amount': discount_amount,
                'final_unit_price': final_unit_price,
                'subtotal': subtotal,
                'total_discount': total_discount,
                'final_total': final_total
            })
    
    return cart_items

def load_categories():
    categories_file = os.path.join('data', 'categories.json')
    if os.path.exists(categories_file):
        with open(categories_file) as f:
            categories = json.load(f)
        
        # Update counts for all categories
        categories_updated = False
        for category in categories:
            products = load_products(category['folder'])
            actual_count = len(products)
            if category.get('count', 0) != actual_count:
                category['count'] = actual_count
                categories_updated = True
        
        # Save updated counts if any were changed
        if categories_updated:
            with open(categories_file, 'w') as f:
                json.dump(categories, f, indent=2)
        
        return categories
    return []

@app.route('/')
def index():
    # Only clear cart if explicitly requested via URL parameter
    if request.args.get('clear_cart') == 'true':
        session['cart'] = {}
        flash('Cart has been cleared.')
    
    categories = load_categories()
    return render_template('index.html', categories=categories)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get admin credentials from environment variables
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if username == admin_username and password == admin_password:
            session['logged_in'] = True
            return redirect(url_for('admin_category'))
        else:
            flash('Invalid credentials')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/category', methods=['GET', 'POST'])
def admin_category():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            folder = request.form.get('folder', '').strip().lower().replace(" ", "_")
            image_file = request.files.get('image')

            # Validate all required fields first
            if not name:
                flash('Category name is required.')
                return redirect(url_for('admin_category'))
            
            if not description:
                flash('Category description is required.')
                return redirect(url_for('admin_category'))
                
            if not folder:
                flash('Category folder name is required.')
                return redirect(url_for('admin_category'))

            if not image_file or not image_file.filename:
                flash('Category image is required.')
                return redirect(url_for('admin_category'))

            # Check if folder already exists
            categories_file = os.path.join('data', 'categories.json')
            if os.path.exists(categories_file):
                with open(categories_file, 'r') as f:
                    existing_categories = json.load(f)
                
                for cat in existing_categories:
                    if cat.get('folder') == folder:
                        flash(f'Category folder "{folder}" already exists. Choose a different folder name.')
                        return redirect(url_for('admin_category'))
            else:
                existing_categories = []

            # STEP 1: First save the image and ensure it succeeds
            print(f"[CATEGORY] Attempting to upload image: {image_file.filename}")
            filename, error = save_uploaded_file(image_file)
            if error:
                flash(f'Image upload failed: {error}')
                return redirect(url_for('admin_category'))
            
            if not filename:
                flash('Image upload failed: No filename returned')
                return redirect(url_for('admin_category'))
            
            # Verify the file was actually saved
            image_path = os.path.join('static', 'images', filename)
            if not os.path.exists(image_path):
                flash('Image upload failed: File was not saved properly')
                return redirect(url_for('admin_category'))
            
            print(f"[CATEGORY] Image uploaded successfully: {filename}")

            # STEP 2: Create data folder only after image upload succeeds
            folder_path = os.path.join('data', folder)
            try:
                os.makedirs(folder_path, exist_ok=True)
                print(f"[CATEGORY] Created folder: {folder_path}")
            except Exception as e:
                # If folder creation fails, clean up the uploaded image
                try:
                    os.remove(image_path)
                except:
                    pass
                flash(f'Failed to create category folder: {str(e)}')
                return redirect(url_for('admin_category'))

            # STEP 3: Update categories.json only after everything else succeeds
            new_category = {
                'name': name,
                'description': description,
                'folder': folder,
                'image': filename,
                'count': 0
            }
            
            existing_categories.append(new_category)
            
            try:
                # Ensure data directory exists
                os.makedirs('data', exist_ok=True)
                
                # Write to a temporary file first, then rename (atomic operation)
                temp_file = categories_file + '.tmp'
                with open(temp_file, 'w') as f:
                    json.dump(existing_categories, f, indent=2)
                
                # Atomic rename
                os.rename(temp_file, categories_file)
                print(f"[CATEGORY] Updated categories.json successfully")
                
            except Exception as e:
                # If JSON update fails, clean up created files
                try:
                    os.remove(image_path)
                    os.rmdir(folder_path)
                except:
                    pass
                flash(f'Failed to save category data: {str(e)}')
                return redirect(url_for('admin_category'))

            flash(f'Category "{name}" added successfully!')
            print(f"[CATEGORY] Category creation complete: {name}")
            return redirect(url_for('admin_category'))
        
        except Exception as e:
            print(f"[CATEGORY ERROR] {str(e)}")
            flash(f'Error adding category: {str(e)}')
            return redirect(url_for('admin_category'))

    categories = load_categories()
    return render_template('admin_category.html', categories=categories)


# Route to display add product form for a category
@app.route('/admin/category/<folder>/add-product')
def add_product_form(folder):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('add_product.html', folder=folder)

    
@app.route('/admin/delete/<folder>', methods=['POST'])
def delete_category(folder):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    categories_file = os.path.join('data', 'categories.json')
    categories = load_categories()
    categories = [cat for cat in categories if cat['folder'] != folder]

    # Save updated list
    with open(categories_file, 'w') as f:
        json.dump(categories, f, indent=2)

    # Optionally remove the folder
    folder_path = os.path.join('data', folder)
    if os.path.exists(folder_path):
        os.rmdir(folder_path)  # Only if folder is empty

    flash('Category deleted successfully.')
    return redirect(url_for('admin_category'))


# Helper functions for products
def load_products(folder):
    products_file = os.path.join('data', folder, 'products.json')
    if os.path.exists(products_file):
        with open(products_file) as f:
            products = json.load(f)
        
        # Ensure all products have required fields with defaults
        updated = False
        for product in products:
            if 'price' not in product:
                product['price'] = 0.0
                updated = True
            if 'weight' not in product:
                product['weight'] = '1.0'
                updated = True
            # Migrate images field (convert single image to images array)
            if 'images' not in product and 'image' in product:
                product['images'] = [product['image']] if product['image'] else []
                updated = True
            elif 'images' not in product:
                product['images'] = []
                updated = True
        
        # Save updated products if any were modified
        if updated:
            save_products(folder, products)
        
        return products
    return []

def save_products(folder, products):
    products_file = os.path.join('data', folder, 'products.json')
    with open(products_file, 'w') as f:
        json.dump(products, f, indent=2)

def update_category_count(folder):
    """Update the product count for a specific category"""
    categories_file = os.path.join('data', 'categories.json')
    categories = load_categories()
    products = load_products(folder)
    
    # Update the count for the specific folder
    for category in categories:
        if category['folder'] == folder:
            category['count'] = len(products)
            break
    
    # Save the updated categories
    with open(categories_file, 'w') as f:
        json.dump(categories, f, indent=2)

@app.route('/admin/manage/<folder>')
def manage_category(folder):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    products = load_products(folder)
    # Annotate each product with estimated shipping cost for default country (e.g., India)
    for product in products:
        weight = 1.0
        if 'weight' in product:
            try:
                weight = float(product['weight'])
            except (ValueError, TypeError):
                pass
        product.setdefault('shipping_cost', {})
        product['shipping_cost']['India'] = get_shipping_cost('India', weight, 1, 'air')
    return render_template('manage_products.html', folder=folder, products=products)


# Route to add a new product in a category
@app.route('/admin/manage/<folder>/add', methods=['GET', 'POST'])
def add_product(folder):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        try:
            # Validate required fields first
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            oem = request.form.get('oem', '').strip()
            weight = request.form.get('weight', '').strip()
            price = request.form.get('price', '').strip()
            
            if not name:
                flash('Product name is required.')
                return redirect(url_for('add_product', folder=folder))
            
            if not description:
                flash('Product description is required.')
                return redirect(url_for('add_product', folder=folder))
                
            if not price:
                flash('Product price is required.')
                return redirect(url_for('add_product', folder=folder))
            
            try:
                stock = int(request.form.get('stock', 0))
                price_float = float(price)
                weight_float = float(weight) if weight else 1.0
            except ValueError:
                flash('Invalid number format for stock, price, or weight.')
                return redirect(url_for('add_product', folder=folder))

            # Process specifications
            spec_categories = request.form.getlist('spec_categories[]')
            specifications = []
            
            print(f"[PRODUCT] Processing specifications: {spec_categories}")
            
            for i, category in enumerate(spec_categories):
                if category.strip():  # Only process non-empty categories
                    options = request.form.getlist(f'spec_options[{i}][]')
                    prices = request.form.getlist(f'spec_prices[{i}][]')
                    weights = request.form.getlist(f'spec_weights[{i}][]')  # Add weight modifiers
                    
                    spec_options = []
                    for j, (option, price_mod, weight_mod) in enumerate(zip(options, prices, weights)):
                        if option.strip():  # Only process non-empty options
                            try:
                                spec_options.append({
                                    'name': option.strip(),
                                    'price_modifier': float(price_mod) if price_mod else 0.0,
                                    'weight_modifier': float(weight_mod) if weight_mod else 0.0
                                })
                            except ValueError:
                                flash(f'Invalid number in specification: {option}')
                                return redirect(url_for('add_product', folder=folder))
                    
                    if spec_options:  # Only add category if it has options
                        specifications.append({
                            'category': category.strip(),
                            'options': spec_options
                        })

            # STEP 1: Handle image uploads first and ensure they all succeed
            image_files = request.files.getlist('images[]')
            valid_image_files = [f for f in image_files if f.filename != '']
            
            if not valid_image_files:
                flash('At least one product image is required.')
                return redirect(url_for('add_product', folder=folder))
            
            uploaded_images = []
            uploaded_file_paths = []  # Keep track for cleanup if needed
            
            print(f"[PRODUCT] Uploading {len(valid_image_files)} images...")
            
            try:
                for i, image_file in enumerate(valid_image_files):
                    if image_file and image_file.filename:
                        print(f"[PRODUCT] Uploading image {i+1}/{len(valid_image_files)}: {image_file.filename}")
                        filename, error = save_uploaded_file(image_file)
                        
                        if error:
                            # Clean up any previously uploaded images
                            for cleanup_path in uploaded_file_paths:
                                try:
                                    os.remove(cleanup_path)
                                except:
                                    pass
                            flash(f'Image upload failed: {error}')
                            return redirect(url_for('add_product', folder=folder))
                        
                        if not filename:
                            # Clean up any previously uploaded images
                            for cleanup_path in uploaded_file_paths:
                                try:
                                    os.remove(cleanup_path)
                                except:
                                    pass
                            flash('Image upload failed: No filename returned')
                            return redirect(url_for('add_product', folder=folder))
                        
                        # Verify the file was actually saved
                        image_path = os.path.join('static', 'images', filename)
                        if not os.path.exists(image_path):
                            # Clean up any previously uploaded images
                            for cleanup_path in uploaded_file_paths:
                                try:
                                    os.remove(cleanup_path)
                                except:
                                    pass
                            flash(f'Image upload failed: File {filename} was not saved properly')
                            return redirect(url_for('add_product', folder=folder))
                        
                        uploaded_images.append(filename)
                        uploaded_file_paths.append(image_path)
                        print(f"[PRODUCT] Image uploaded successfully: {filename}")
                        
            except Exception as e:
                # Clean up any uploaded images
                for cleanup_path in uploaded_file_paths:
                    try:
                        os.remove(cleanup_path)
                    except:
                        pass
                flash(f'Error during image upload: {str(e)}')
                return redirect(url_for('add_product', folder=folder))

            print(f"[PRODUCT] All {len(uploaded_images)} images uploaded successfully")

            # STEP 2: Create product data only after all images are uploaded successfully
            new_product = {
                'name': name,
                'description': description,
                'oem': oem,
                'weight': weight,
                'price': price_float,
                'stock': stock,
                'image': uploaded_images[0] if uploaded_images else '',  # Main image for backward compatibility
                'images': uploaded_images,  # Array of all images
                'specifications': specifications,
                'shipping': {
                    'weight_kg': weight_float,
                    'excluded_countries': EXCLUDED_COUNTRIES,
                    'rate_per_1000km_per_kg': SHIPPING_RATE_PER_1000KM_PER_KG,
                    'shipping_discount': SHIPPING_DISCOUNT
                }
            }

            # STEP 3: Load existing products and add new one
            try:
                products = load_products(folder)
                products.append(new_product)
                
                # Save products atomically
                products_file = os.path.join('data', folder, 'products.json')
                temp_file = products_file + '.tmp'
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(products_file), exist_ok=True)
                
                with open(temp_file, 'w') as f:
                    json.dump(products, f, indent=2)
                
                # Atomic rename
                os.rename(temp_file, products_file)
                print(f"[PRODUCT] Saved products.json successfully")
                
                # Update category count
                update_category_count(folder)
                
                flash(f'Product "{name}" added successfully!')
                print(f"[PRODUCT] Product creation complete: {name}")
                return redirect(url_for('manage_category', folder=folder))
                
            except Exception as e:
                # If product save fails, clean up uploaded images
                for cleanup_path in uploaded_file_paths:
                    try:
                        os.remove(cleanup_path)
                    except:
                        pass
                flash(f'Failed to save product data: {str(e)}')
                return redirect(url_for('add_product', folder=folder))
                
        except Exception as e:
            print(f"[PRODUCT ERROR] {str(e)}")
            flash(f'Error adding product: {str(e)}')
            return redirect(url_for('add_product', folder=folder))

    return render_template('add_product.html', folder=folder)

@app.route('/admin/manage/<folder>/edit/<slug>', methods=['GET', 'POST'])
def edit_product(folder, slug):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    products = load_products(folder)
    product = None
    product_index = None
    
    # Find product by slug
    for i, p in enumerate(products):
        if slugify(p['name']) == slug:
            product = p
            product_index = i
            break
    
    if not product:
        flash('Product not found.')
        return redirect(url_for('manage_category', folder=folder))
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form['description'].strip()
        oem = request.form.get('oem', '').strip()
        weight = request.form['weight'].strip()
        price = request.form['price'].strip()
        stock = int(request.form['stock'])
        image_file = request.files.get('image')
        
        # Process specifications
        spec_categories = request.form.getlist('spec_categories[]')
        specifications = []
        
        print(f"DEBUG EDIT_PRODUCT: spec_categories = {spec_categories}")
        print(f"DEBUG EDIT_PRODUCT: Full form data = {dict(request.form)}")
        
        for i, category in enumerate(spec_categories):
            if category.strip():  # Only process non-empty categories
                options = request.form.getlist(f'spec_options[{i}][]')
                prices = request.form.getlist(f'spec_prices[{i}][]')
                weights = request.form.getlist(f'spec_weights[{i}][]')  # Add weight modifiers
                
                print(f"DEBUG EDIT_PRODUCT: Category {i} '{category}' - options: {options}, prices: {prices}, weights: {weights}")
                
                spec_options = []
                for j, (option, price_mod, weight_mod) in enumerate(zip(options, prices, weights)):
                    if option.strip():  # Only process non-empty options
                        spec_options.append({
                            'name': option.strip(),
                            'price_modifier': float(price_mod) if price_mod else 0.0,
                            'weight_modifier': float(weight_mod) if weight_mod else 0.0
                        })
                
                if spec_options:  # Only add category if it has options
                    specifications.append({
                        'category': category.strip(),
                        'options': spec_options
                    })
        
        print(f"DEBUG EDIT_PRODUCT: Final specifications = {specifications}")
        
        if not name or not description or not price:
            flash('Name, description, and price are required.')
            return redirect(url_for('edit_product', folder=folder, slug=slug))
        
        # Update product data
        products[product_index]['name'] = name
        products[product_index]['description'] = description
        products[product_index]['oem'] = oem
        products[product_index]['weight'] = weight
        products[product_index]['price'] = float(price) if price else 0.0
        products[product_index]['stock'] = stock
        products[product_index]['specifications'] = specifications
        
        # Handle image updates
        image_files = request.files.getlist('images[]')
        valid_image_files = [f for f in image_files if f.filename != '']
        
        # Get which existing images to keep
        images_to_keep = request.form.getlist('keep_images[]')
        
        # Start with existing images that user wants to keep
        existing_images = []
        if images_to_keep:
            existing_images = images_to_keep
        elif not valid_image_files:
            # If no new images and no keep_images specified, keep all existing images
            existing_images = products[product_index].get('images', [])
            if not existing_images and products[product_index].get('image'):
                existing_images = [products[product_index]['image']]
        
        # Add new uploaded images
        uploaded_images = []
        if valid_image_files:
            try:
                for image_file in valid_image_files:
                    if image_file and image_file.filename:
                        filename, error = save_uploaded_file(image_file)
                        if error:
                            flash(f'Image upload failed: {error}')
                            return redirect(url_for('edit_product', folder=folder, slug=slug))
                        uploaded_images.append(filename)
            except Exception as e:
                flash(f'Error uploading images: {str(e)}')
                return redirect(url_for('edit_product', folder=folder, slug=slug))
        
        # Combine kept existing images and new images
        all_images = existing_images + uploaded_images
        
        # Update both image formats for compatibility
        if all_images:
            products[product_index]['image'] = all_images[0]
            products[product_index]['images'] = all_images
        else:
            # If no images at all, keep the original structure
            products[product_index]['image'] = products[product_index].get('image', '')
            products[product_index]['images'] = products[product_index].get('images', [])
        
        # Update shipping info
        products[product_index]['shipping'] = {
            'weight_kg': float(weight) if weight else 1.0,
            'excluded_countries': EXCLUDED_COUNTRIES,
            'rate_per_1000km_per_kg': SHIPPING_RATE_PER_1000KM_PER_KG,
            'shipping_discount': SHIPPING_DISCOUNT
        }
        
        save_products(folder, products)
        update_category_count(folder)
        flash('Product updated successfully!')
        return redirect(url_for('manage_category', folder=folder))
    
    return render_template('edit_product.html', folder=folder, product=product)

@app.route('/admin/manage/<folder>/delete/<slug>', methods=['GET', 'POST'])
def delete_product(folder, slug):
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    products = load_products(folder)
    product_index = None
    
    # Find product by slug
    for i, p in enumerate(products):
        if slugify(p['name']) == slug:
            product_index = i
            break
    
    if product_index is not None:
        products.pop(product_index)
        save_products(folder, products)
        update_category_count(folder)
        flash('Product deleted successfully!')
    else:
        flash('Product not found.')
    
    return redirect(url_for('manage_category', folder=folder))

@app.route('/fabrication')
def fabrication():
    return render_template('fabrication.html')

@app.route('/custom-clamps')
def custom_clamps():
    return render_template('custom_clamps.html')

@app.route('/products')
def products():
    """Display all product categories"""
    categories = load_categories()
    return render_template('products.html', categories=categories)

@app.route('/products/<category_folder>')
def category_products(category_folder):
    """Display products in a specific category"""
    categories = load_categories()
    category = None
    
    # Find the category
    for cat in categories:
        if cat['folder'] == category_folder:
            category = cat
            break
    
    if not category:
        flash('Category not found.')
        return redirect(url_for('products'))
    
    products = load_products(category_folder)
    
    # Add shipping cost for India to each product for display
    for product in products:
        weight = 1.0
        if 'weight' in product:
            try:
                weight = float(product['weight'])
            except (ValueError, TypeError):
                pass
        product['india_shipping'] = get_shipping_cost('India', weight, 1, 'air')
    
    return render_template('category_products.html', category=category, products=products)

@app.route('/product/<category_folder>/<product_slug>')
def product_detail(category_folder, product_slug):
    """Display individual product details"""
    categories = load_categories()
    category = None
    
    # Find the category
    for cat in categories:
        if cat['folder'] == category_folder:
            category = cat
            break
    
    if not category:
        flash('Category not found.')
        return redirect(url_for('products'))
    
    products = load_products(category_folder)
    product = None
    
    # Find the product by slug
    for p in products:
        if slugify(p['name']) == product_slug:
            product = p
            break
    
    if not product:
        flash('Product not found.')
        return redirect(url_for('category_products', category_folder=category_folder))
    
    # Calculate shipping costs for sample countries
    weight = 1.0
    if 'weight' in product:
        try:
            weight = float(product['weight'])
        except (ValueError, TypeError):
            pass
    
    sample_shipping = {
        'India': get_shipping_cost('India', weight, 1, 'air'),
        'United States': get_shipping_cost('United States', weight, 1, 'air'),
        'Germany': get_shipping_cost('Germany', weight, 1, 'air'),
        'Australia': get_shipping_cost('Australia', weight, 1, 'air')
    }
    
    return render_template('product_detail.html', 
                         category=category, 
                         product=product, 
                         product_slug=product_slug,  # Pass the slug to template
                         sample_shipping=sample_shipping)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # handle contact form submission (email or DB storage)
        contact_data = {
            'name': request.form.get("name"),
            'email': request.form.get("email"),
            'phone': request.form.get("phone"),
            'inquiry': request.form.get("inquiry"),
            'message': request.form.get("message")
        }
        
        # Send email notification to sales team
        email_sent = send_contact_notification(contact_data)
        
        if email_sent:
            flash("Thank you for your message. We'll get back to you soon!", "success")
        else:
            flash("Thank you for your message. We'll get back to you soon!", "success")
            # Still show success message to user even if email fails
        
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/shipping-info/<country>")
def shipping_info(country):
    """API endpoint to check shipping availability and cost"""
    country = country.strip().title()
    weight = float(request.args.get('weight', 1.0))  # Default to 1kg if not specified
    method = request.args.get('method', 'air').lower()  # Default to air shipping
    quantity = int(request.args.get('quantity', get_cart_total_quantity() or 1))  # Get cart quantity or default to 1
    
    if is_shipping_allowed(country):
        cost = calculate_shipping_cost(country, weight, quantity, method)
        
        distance = get_shipping_distance(country)
        shipping_weight = math.ceil(weight) if weight > 0 else 1
        
        # Create calculation explanation
        if country.lower() == 'india':
            base_calculation = f"$2.50 × {shipping_weight}kg (India domestic rate)"
        else:
            base_rate = (distance / 1000) * shipping_weight * SHIPPING_RATE_PER_1000KM_PER_KG
            base_calculation = f"${SHIPPING_RATE_PER_1000KM_PER_KG} × {distance/1000:.1f} (1000km units) × {shipping_weight}kg = ${base_rate:.2f}, with 50% discount"
        
        if method == 'sea':
            calculation_text = f"{base_calculation}, Sea shipping (16% of air cost) = ${cost}"
        elif method == 'air' and quantity >= 50:
            # Show quantity discount for air shipping
            discount_rate = 0.0
            if quantity >= 5000:
                discount_rate = 0.92
            elif quantity >= 3000:
                discount_rate = 0.91
            elif quantity >= 2000:
                discount_rate = 0.90
            elif quantity >= 1500:
                discount_rate = 0.89
            elif quantity >= 1000:
                discount_rate = 0.88
            elif quantity >= 500:
                discount_rate = 0.29
            elif quantity >= 200:
                discount_rate = 0.18
            elif quantity >= 100:
                discount_rate = 0.14
            elif quantity >= 50:
                discount_rate = 0.08
            
            if discount_rate > 0:
                calculation_text = f"{base_calculation}, Quantity discount ({int(discount_rate*100)}% for {quantity} pcs) = ${cost}"
            else:
                calculation_text = f"{base_calculation} = ${cost}"
        else:
            calculation_text = f"{base_calculation} = ${cost}"
        
        return {
            "allowed": True,
            "country": country,
            "weight_kg": weight,
            "shipping_weight_kg": shipping_weight,
            "distance_km": distance,
            "shipping_cost": cost,
            "method": method,
            "currency": "USD",
            "calculation": calculation_text
        }
    else:
        return {
            "allowed": False,
            "country": country,
            "message": f"Sorry, we do not ship to {country}"
        }

@app.route("/shipping-policy")
def shipping_policy():
    """Display shipping policy page"""
    return render_template("shipping_policy.html", 
                         excluded_countries=EXCLUDED_COUNTRIES,
                         rate_per_1000km_per_kg=SHIPPING_RATE_PER_1000KM_PER_KG,
                         shipping_discount=SHIPPING_DISCOUNT)

# Cart routes
@app.route("/add-to-cart", methods=["POST"])
def add_to_cart_route():
    """Add item to cart via AJAX"""
    try:
        data = request.get_json()
        category_folder = data.get('category_folder')
        product_slug = data.get('product_slug')
        quantity = int(data.get('quantity', 1))
        specifications = data.get('specifications', {})
        shipping = data.get('shipping', {})
        
        cart_key = add_to_cart(category_folder, product_slug, quantity, specifications, shipping)
        cart_count = len(get_cart())
        
        return jsonify({
            'success': True,
            'message': f'Added {quantity} item(s) to cart',
            'cart_count': cart_count,
            'cart_key': cart_key
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@app.route("/cart")
def cart():
    """Display cart page"""
    cart_items = get_cart_items_with_details()
    cart_total = get_cart_total()
    products_total = get_cart_products_total()
    shipping_total = get_cart_shipping_total()
    
    # Calculate total weight for shipping (including specification modifiers)
    total_weight = 0
    for item in cart_items:
        total_weight += item['total_weight']
    
    return render_template('cart.html', 
                         cart_items=cart_items, 
                         cart_total=cart_total,
                         products_total=products_total,
                         shipping_total=shipping_total,
                         total_weight=total_weight)

@app.route("/update-cart", methods=["POST"])
def update_cart():
    """Update cart item quantity"""
    try:
        data = request.get_json()
        cart_key = data.get('cart_key')
        quantity = int(data.get('quantity', 0))
        
        update_cart_quantity(cart_key, quantity)
        
        # Recalculate totals
        cart_items = get_cart_items_with_details()
        cart_total = get_cart_total()
        products_total = get_cart_products_total()
        shipping_total = get_cart_shipping_total()
        
        return jsonify({
            'success': True,
            'cart_total': cart_total,
            'products_total': products_total,
            'shipping_total': shipping_total,
            'cart_count': len(get_cart())
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@app.route("/remove-from-cart", methods=["POST"])
def remove_from_cart_route():
    """Remove item from cart"""
    try:
        data = request.get_json()
        cart_key = data.get('cart_key')
        
        remove_from_cart(cart_key)
        
        return jsonify({
            'success': True,
            'cart_count': len(get_cart()),
            'cart_total': get_cart_total()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@app.route("/clear-cart")
def clear_cart():
    """Clear the cart (for testing purposes)"""
    session['cart'] = {}
    flash('Cart cleared successfully.')
    return redirect(url_for('cart'))

@app.route("/checkout")
def checkout():
    """Display checkout page"""
    cart_items = get_cart_items_with_details()
    
    if not cart_items:
        flash('Your cart is empty.')
        return redirect(url_for('cart'))
    
    products_total = get_cart_products_total()  # Products only, no shipping
    shipping_total = get_cart_shipping_total()  # Shipping only
    cart_total = products_total + shipping_total  # Combined total
    
    # Calculate total weight for shipping (including specification modifiers)
    total_weight = 0
    for item in cart_items:
        total_weight += item['total_weight']
    
    return render_template('checkout.html', 
                         cart_items=cart_items, 
                         products_total=products_total,
                         shipping_total=shipping_total,
                         cart_total=cart_total,
                         total_weight=total_weight)

@app.route("/place-order", methods=["POST"])
def place_order():
    """Process order placement"""
    cart_items = get_cart_items_with_details()
    
    if not cart_items:
        flash('Your cart is empty.')
        return redirect(url_for('cart'))
    
    # Get form data
    customer_info = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'phone': request.form.get('phone'),
        'company': request.form.get('company', ''),
        'address': request.form.get('address'),
        'city': request.form.get('city'),
        'state': request.form.get('state'),
        'country': request.form.get('country'),
        'postal_code': request.form.get('postal_code'),
        'shipping_method': request.form.get('shipping_method', 'air'),
        'payment_method': request.form.get('payment_method', 'cod'),
        'notes': request.form.get('notes', '')
    }
    
    # Validate required fields
    required_fields = ['name', 'email', 'phone', 'address', 'city', 'country']
    for field in required_fields:
        if not customer_info[field]:
            flash(f'{field.replace("_", " ").title()} is required.')
            return redirect(url_for('checkout'))
    
    # Calculate totals
    cart_total = get_cart_products_total()  # Products only, no shipping
    total_weight = sum(item['total_weight'] for item in cart_items)
    total_quantity = get_cart_total_quantity()
    
    # Calculate shipping with quantity-based pricing
    shipping_cost = calculate_shipping_cost(customer_info['country'], total_weight, total_quantity, customer_info['shipping_method'])
    
    # Handle payment method
    payment_status = 'pending'
    payment_info = {
        'method': customer_info['payment_method'],
        'status': payment_status,
        'amount': cart_total + shipping_cost
    }
    
    # Add payment-specific information
    if customer_info['payment_method'] == 'cod':
        payment_info['instructions'] = 'Pay cash on delivery when you receive your order.'
    elif customer_info['payment_method'] == 'paypal':
        # Create PayPal payment
        return_url = url_for('paypal_success', _external=True)
        cancel_url = url_for('paypal_cancel', _external=True)
        
        # Create temporary order ID for PayPal
        temp_order_id = f"ORD-{int(time.time())}"
        
        paypal_payment = create_paypal_payment(
            cart_total + shipping_cost,
            temp_order_id,
            return_url,
            cancel_url
        )
        
        if paypal_payment:
            # Store order data in session for completion after PayPal approval
            session['pending_order'] = {
                'order_id': temp_order_id,
                'customer_info': customer_info,
                'cart_items': cart_items,
                'cart_total': cart_total,
                'shipping_cost': shipping_cost,
                'total_weight': total_weight,
                'payment_id': paypal_payment.id
            }
            
            # Redirect to PayPal for approval
            for link in paypal_payment.links:
                if link.rel == "approval_url":
                    return redirect(link.href)
        else:
            flash('Error creating PayPal payment. Please try again or choose a different payment method.')
            return redirect(url_for('checkout'))
            
    elif customer_info['payment_method'] == 'upi':
        payment_info['instructions'] = 'Please pay using UPI and send payment screenshot via email.'
        payment_info['upi_id'] = 'qualityclamps@upi'
        payment_info['upi_name'] = 'Quality Clamps'
    elif customer_info['payment_method'] == 'email':
        payment_info['instructions'] = 'We will contact you directly for bulk pricing negotiation and payment terms. Check your email within 2 hours for personalized pricing and payment options.'
        payment_info['contact_email'] = 'orders@qualclamps.com'
        payment_info['note'] = 'Bulk orders qualify for special pricing and flexible payment terms'
    
    # Create order
    order = {
        'order_id': f"ORD-{int(time.time())}",
        'customer_info': customer_info,
        'order_items': cart_items,
        'subtotal': cart_total,
        'shipping_cost': shipping_cost,
        'total': cart_total + shipping_cost,
        'total_weight': total_weight,
        'payment_info': payment_info,
        'status': 'pending',
        'created_at': time.time(),
        'created_date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save order (you might want to save to database instead)
    orders_file = 'data/orders.json'
    if os.path.exists(orders_file):
        with open(orders_file, 'r') as f:
            orders = json.load(f)
    else:
        orders = []
    
    orders.append(order)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    with open(orders_file, 'w') as f:
        json.dump(orders, f, indent=2)
    
    # Send email notification to sales team
    send_order_notification(order)
    
    # Clear cart
    session['cart'] = {}
    
    flash(f'Order {order["order_id"]} placed successfully! We will contact you soon.')
    return render_template('order_confirmation.html', order=order)

@app.route('/paypal/success')
def paypal_success():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')
    
    if not payment_id or not payer_id:
        flash('Payment verification failed. Please try again.')
        return redirect(url_for('checkout'))
    
    # Get pending order from session
    pending_order = session.get('pending_order')
    if not pending_order or pending_order['payment_id'] != payment_id:
        flash('Order information not found. Please try again.')
        return redirect(url_for('checkout'))
    
    # Execute PayPal payment
    if execute_paypal_payment(payment_id, payer_id):
        # Payment successful, create the order
        order_data = {
            'order_id': pending_order['order_id'],
            'customer_info': pending_order['customer_info'],
            'order_items': pending_order['cart_items'],
            'subtotal': pending_order['cart_total'],  # This is products total
            'shipping_cost': pending_order['shipping_cost'],
            'total': pending_order['cart_total'] + pending_order['shipping_cost'],
            'total_weight': pending_order['total_weight'],
            'payment_info': {
                'method': 'PayPal',
                'status': 'Paid',
                'transaction_id': payment_id,
                'amount': pending_order['cart_total'] + pending_order['shipping_cost']
            }
        }
        
        # Send email notification to sales team
        send_order_notification(order_data)
        
        # Clear session data
        session.pop('cart', None)
        session.pop('pending_order', None)
        
        return render_template('order_confirmation.html', order=order_data)
    else:
        flash('Payment processing failed. Please try again.')
        return redirect(url_for('checkout'))

@app.route('/paypal/cancel')
def paypal_cancel():
    # Clear pending order if user cancels
    session.pop('pending_order', None)
    flash('Payment was cancelled. Your order has not been placed.')
    return redirect(url_for('checkout'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)