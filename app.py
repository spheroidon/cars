from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['JWT_SECRET_KEY'] = 'change_in_production'  # Change this to a secret key of your choice
jwt = JWTManager(app)
db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

    customers = relationship('Customer', back_populates='admin', cascade='all, delete-orphan')

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(255), nullable=True)

    cars = relationship('Car', back_populates='customer', cascade='all, delete-orphan')

    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    admin = relationship('Admin', back_populates='customers')

class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255), nullable=True)

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = relationship('Customer', back_populates='cars')


# Image Upload Helper Function
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/', methods=['GET'])
def show_homepage():
    return render_template('index.html')

@app.route('/customers', methods=['GET', 'POST'])
@jwt_required()
def handle_customers():
    current_admin_id = get_jwt_identity()

    if request.method == 'GET':
        customers = Customer.query.filter_by(admin_id=current_admin_id).all()
        customers_list = [{'id': customer.id, 'name': customer.name, 'email': customer.email, 'image': customer.image} for customer in customers]
        return jsonify(customers_list)
    elif request.method == 'POST':
        data = request.form
        new_customer = Customer(name=data['name'], email=data['email'], admin_id=current_admin_id)

        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_customer.image = filename

        db.session.add(new_customer)
        db.session.commit()
        return jsonify({'message': 'Customer added successfully'}), 201

@app.route('/customers/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_customer(id):
    current_admin_id = get_jwt_identity()
    customer = Customer.query.get_or_404(id)

    if customer.admin_id != current_admin_id:
        return jsonify({'message': 'Unauthorized access'}), 403

    if request.method == 'GET':
        return jsonify({'id': customer.id, 'name': customer.name, 'email': customer.email, 'image': customer.image})
    elif request.method == 'PUT':
        data = request.form
        customer.name = data['name']
        customer.email = data['email']

        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                customer.image = filename

        db.session.commit()
        return jsonify({'message': 'Customer updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'message': 'Customer deleted successfully'})

# Car routes
@app.route('/cars', methods=['GET', 'POST'])
@jwt_required()
def handle_cars():
    current_admin_id = get_jwt_identity()

    if request.method == 'GET':
        cars = Car.query.join(Customer).filter(Customer.admin_id == current_admin_id).all()
        cars_list = [{'id': car.id, 'brand': car.brand, 'model': car.model, 'year': car.year, 'image': car.image, 'customer_id': car.customer_id,'customer': car.customer.name} for car in cars]
        return jsonify(cars_list)
    elif request.method == 'POST':
        data = request.form
        new_car = Car(brand=data['brand'], model=data['model'], year=data['year'], customer_id=data['customer_id'])

        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                new_car.image = filename

        db.session.add(new_car)
        db.session.commit()
        return jsonify({'message': 'Car added successfully'}), 201

@app.route('/cars/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def handle_car(id):
    current_admin_id = get_jwt_identity()
    car = Car.query.join(Customer).filter(Customer.admin_id == current_admin_id, Car.id == id).first_or_404()

    if request.method == 'GET':
        return jsonify({'id': car.id, 'brand': car.brand, 'model': car.model, 'year': car.year, 'image': car.image, 'customer_id': car.customer_id})
    elif request.method == 'PUT':
        data = request.form
        car.brand = data['brand']
        car.model = data['model']
        car.year = data['year']
        car.customer_id = data['customer_id']

        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                car.image = filename

        db.session.commit()
        return jsonify({'message': 'Car updated successfully'})
    elif request.method == 'DELETE':
        db.session.delete(car)
        db.session.commit()
        return jsonify({'message': 'Car deleted successfully'})


@app.route('/admin/register', methods=['POST'])
def register_admin():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    new_admin = Admin(email=email, password=password)
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({'message': 'Admin registered successfully'}), 201

# Admin login route
@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    admin = Admin.query.filter_by(email=email, password=password).first()

    if admin:
        access_token = create_access_token(identity=admin.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=5240)
