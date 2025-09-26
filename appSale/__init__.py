
from flask import Flask
from urllib.parse import quote
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:%s@localhost/dbsaleapp?charset=utf8mb4" % quote('16122003')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['PAGE_SIZE'] = 4
app.secret_key = '@##$@#$@#$@%$%$%^%^&%^&%&$%%'



db =SQLAlchemy(app=app)

login = LoginManager(app=app)

app.config['CART_KEY'] = 'cart'

cloudinary.config(
    cloud_name="dr1dlhww5",
    api_key="996698978232863",
    api_secret="QsQHT5Zur10MvH1zIHhiVg28wBs"
)
