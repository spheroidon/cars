import json
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
CORS(app)

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

# Define Models
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(255), nullable=True)

    cars = relationship('Car', back_populates='customer', cascade='all, delete-orphan')

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
def handle_customers():
    if request.method == 'GET':
        customers = Customer.query.all()
        customers_list = [{'id': customer.id, 'name': customer.name, 'email': customer.email, 'image': customer.image} for customer in customers]
        return jsonify(customers_list)
    elif request.method == 'POST':
        data = request.form
        new_customer = Customer(name=data['name'], email=data['email'])
        
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
def handle_customer(id):
    customer = Customer.query.get_or_404(id)

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

@app.route('/cars', methods=['GET', 'POST'])
def handle_cars():
    if request.method == 'GET':
        cars = Car.query.all()
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
def handle_car(id):
    car = Car.query.get_or_404(id)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,port=5240)
