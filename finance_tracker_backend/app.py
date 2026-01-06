import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User, Transaction
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
# 3. Then do your database config
db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:1234@localhost/finance_tracker')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY','development-secret-key')

app.config['JWT_TOKEN_LOCATION'] = ['headers'] 
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)  # Token expires in 7 days

# Initialize extensions
#CORS(app, resources={r"/api/*": {"origins": "*"}})
CORS(app, origins=["https://personal-finance-tracker-6-y8oy.onrender.com"], supports_credentials=True)
db.init_app(app)
jwt = JWTManager(app)

# Create tables
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully!")


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500


# ==================== AUTH ROUTES ====================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        if not data.get('password'):
            return jsonify({'error': 'Password is required'}), 400
        
        # Validate email format
        if '@' not in data['email']:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password length
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email'].lower()).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            name=data['name'].strip(),
            email=data['email'].lower().strip()
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        if not data.get('password'):
            return jsonify({'error': 'Password is required'}), 400
        
        # Find user
        user = User.query.filter_by(email=data['email'].lower().strip()).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


# ==================== TRANSACTION ROUTES ====================

@app.route('/api/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get all transactions for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters for filtering
        transaction_type = request.args.get('type')
        category = request.args.get('category')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Base query
        query = Transaction.query.filter_by(user_id=current_user_id)
        
        # Apply filters
        if transaction_type:
            query = query.filter_by(type=transaction_type)
        if category:
            query = query.filter_by(category=category)
        if start_date:
            query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # Get transactions ordered by date (newest first)
        transactions = query.order_by(Transaction.date.desc()).all()
        
        return jsonify({
            'transactions': [t.to_dict() for t in transactions],
            'count': len(transactions)
        }), 200
        
    except Exception as e:
        print(f"Get transactions error: {str(e)}")
        return jsonify({'error': 'Failed to fetch transactions'}), 500


@app.route('/api/transactions', methods=['POST'])
@jwt_required()
def create_transaction():
    """Create a new transaction"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validation
        if not data.get('type'):
            return jsonify({'error': 'Transaction type is required'}), 400
        if not data.get('category'):
            return jsonify({'error': 'Category is required'}), 400
        if not data.get('amount'):
            return jsonify({'error': 'Amount is required'}), 400
        if not data.get('date'):
            return jsonify({'error': 'Date is required'}), 400
        
        # Validate transaction type
        valid_types = ['income', 'expense', 'savings', 'investment']
        if data['type'] not in valid_types:
            return jsonify({'error': 'Invalid transaction type'}), 400
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400
        
        # Create transaction
        transaction = Transaction(
            user_id=current_user_id,
            type=data['type'],
            category=data['category'],
            amount=amount,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            description=data.get('description', '').strip()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Transaction created successfully',
            'transaction': transaction.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Create transaction error: {str(e)}")
        return jsonify({'error': 'Failed to create transaction'}), 500


@app.route('/api/transactions/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get a specific transaction"""
    try:
        current_user_id = get_jwt_identity()
        
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=current_user_id
        ).first()
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        return jsonify({'transaction': transaction.to_dict()}), 200
        
    except Exception as e:
        print(f"Get transaction error: {str(e)}")
        return jsonify({'error': 'Failed to fetch transaction'}), 500


@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
@jwt_required()
def update_transaction(transaction_id):
    """Update a transaction"""
    try:
        current_user_id = get_jwt_identity()
        
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=current_user_id
        ).first()
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'type' in data:
            valid_types = ['income', 'expense', 'savings', 'investment']
            if data['type'] not in valid_types:
                return jsonify({'error': 'Invalid transaction type'}), 400
            transaction.type = data['type']
        
        if 'category' in data:
            transaction.category = data['category']
        
        if 'amount' in data:
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    return jsonify({'error': 'Amount must be greater than 0'}), 400
                transaction.amount = amount
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid amount format'}), 400
        
        if 'date' in data:
            try:
                transaction.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if 'description' in data:
            transaction.description = data['description'].strip()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Transaction updated successfully',
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update transaction error: {str(e)}")
        return jsonify({'error': 'Failed to update transaction'}), 500


@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    """Delete a transaction"""
    try:
        current_user_id = get_jwt_identity()
        
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=current_user_id
        ).first()
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({'message': 'Transaction deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete transaction error: {str(e)}")
        return jsonify({'error': 'Failed to delete transaction'}), 500


# ==================== STATISTICS ROUTES ====================

@app.route('/api/stats/summary', methods=['GET'])
@jwt_required()
def get_stats_summary():
    """Get summary statistics for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters for date filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Base query
        query = Transaction.query.filter_by(user_id=current_user_id)
        
        # Apply date filters
        if start_date:
            query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        transactions = query.all()
        
        # Calculate totals
        total_income = sum(float(t.amount) for t in transactions if t.type == 'income')
        total_expense = sum(float(t.amount) for t in transactions if t.type == 'expense')
        total_savings = sum(float(t.amount) for t in transactions if t.type == 'savings')
        total_investment = sum(float(t.amount) for t in transactions if t.type == 'investment')
        balance = total_income - total_expense - total_savings - total_investment
        
        return jsonify({
            'total_income': total_income,
            'total_expense': total_expense,
            'total_savings': total_savings,
            'total_investment': total_investment,
            'balance': balance,
            'transaction_count': len(transactions)
        }), 200
        
    except Exception as e:
        print(f"Get stats error: {str(e)}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500


@app.route('/api/stats/by-category', methods=['GET'])
@jwt_required()
def get_stats_by_category():
    """Get statistics grouped by category"""
    try:
        current_user_id = get_jwt_identity()
        transaction_type = request.args.get('type', 'expense')  # Default to expense
        
        # Get transactions of specified type
        transactions = Transaction.query.filter_by(
            user_id=current_user_id,
            type=transaction_type
        ).all()
        
        # Group by category
        category_stats = {}
        for t in transactions:
            if t.category not in category_stats:
                category_stats[t.category] = 0
            category_stats[t.category] += float(t.amount)
        
        # Convert to list format
        result = [
            {'category': category, 'total': amount}
            for category, amount in category_stats.items()
        ]
        
        return jsonify({
            'type': transaction_type,
            'categories': result
        }), 200
        
    except Exception as e:
        print(f"Get category stats error: {str(e)}")
        return jsonify({'error': 'Failed to fetch category statistics'}), 500


# ==================== USER ROUTES ====================

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        print(f"Get profile error: {str(e)}")
        return jsonify({'error': 'Failed to fetch profile'}), 500


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        # Test database connection (SQLAlchemy 2.0 compatible)
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'ok',
            'message': 'Backend is running',
            'database': 'PostgreSQL connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'database': 'Connection failed'
        }), 500


@app.route('/', methods=['GET'])
def home():
    """API information endpoint"""
    return jsonify({
        'message': 'Personal Finance Tracker API',
        'version': '1.0',
        'endpoints': {
            'auth': {
                'register': 'POST /api/register',
                'login': 'POST /api/login'
            },
            'transactions': {
                'list': 'GET /api/transactions',
                'create': 'POST /api/transactions',
                'get': 'GET /api/transactions/<id>',
                'update': 'PUT /api/transactions/<id>',
                'delete': 'DELETE /api/transactions/<id>'
            },
            'stats': {
                'summary': 'GET /api/stats/summary',
                'by_category': 'GET /api/stats/by-category'
            },
            'user': {
                'profile': 'GET /api/user/profile'
            }
        }
    }), 200


if __name__ == '__main__':
    print("🚀 Starting Personal Finance Tracker Backend...")
    print("📊 Database: PostgreSQL")
    print("🔐 Authentication: JWT")
    print("🌐 Server: http://localhost:5000")
    print("=" * 50)
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    #app.run(debug=True, host='0.0.0.0', port=5000)
