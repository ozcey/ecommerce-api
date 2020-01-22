import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from sqlalchemy.orm import relationship

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ecommerce.db')
app.config['JWT_SECRET_KEY'] = '4ea8d2335b430796cf3f500368c5b0f5b1dc90f5'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("Database created!")


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print("Database dropped!")


@app.route('/', methods=['GET'])
def welcome():
    return 'Welcome to E-Commerce App'


@app.route('/home', methods=['GET'])
def home():
    return 'Welcome to Home Page'


@app.route('/find_users', methods=['GET'])
def retrieve_users():
    users_list = User.query.all()
    response = users_schema.dump(users_list)
    return jsonify(response)


@app.route('/findUserById/<int:id>', methods=['GET'])
def retrieve_user(id: int):
    user = User.query.filter_by(id=id).first()
    if user:
        response = user_schema.dump(user)
        return jsonify(response)
    else:
        return jsonify(message="That user doesn't exist!"), 404


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password'] 
    else:
        email = request.form['email']
        password = request.form['password']
    user = User.query.filter_by(email=email, password=password).first()
    if user:
        access_token = create_access_token(identity=email)
        return jsonify(message="You logged in successfully!", access_token=access_token)
    else:
        return jsonify(message="Bad email or password!"), 401


@app.route('/create_user', methods=['POST'])
@jwt_required
def create_user():
    email = request.form['email']
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify(message="That user already exist!"), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        role = request.form['role']
        new_user = User(first_name=first_name, last_name=last_name, 
                        email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(message="User created successfully!"), 201


@app.route('/update_user', methods=['PUT'])
@jwt_required
def update_user():
    user_id = int(request.form['id'])
    user = User.query.filter_by(id=user_id).first()
    if user:
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.password = request.form['password']
        user.role = request.form['role']
        db.session.commit()
        return jsonify(message="The user updated successfully!"), 202
    else:
        return jsonify(message="The user doesn't exist!"), 401


@app.route('/delete_user/<int:id>', methods=['DELETE'])
@jwt_required
def remove_user(id: int):
    user = User.query.filter_by(id=id).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify(message="The user has been deleted!"), 202
    else:
        return jsonify(message="The user doesn't exist!"), 404


class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    address = relationship("Address", backref='customers', lazy=True)


class Address(db.Model):
    __tablename__ = 'address'
    id = Column(Integer, primary_key=True)
    street = Column(String)
    city = Column(String)
    state = Column(String)
    zipcode = Column(String)
    customer_id = Column(Integer, ForeignKey('customer_id'), nullable=False)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password', 'role')


class CustomerSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password', 'address')


class AddressSchema(ma.Schema):
    class Meta:
        fields = ('id', 'street', 'city', 'state', 'zipcode', 'customer_id')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


if __name__ == '__main__':
    app.run()
