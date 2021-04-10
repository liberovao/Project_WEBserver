import os
import uuid

from flask import Flask, render_template, redirect, flash, url_for, session, send_from_directory, request
from flask_apscheduler import APScheduler
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeSerializer

from db import db, User, db2, D_writers, update_session
from loginform import LoginForm
from regform import RegForm
from config import Config


MAX_CONTENT_LENGTH_FOR_AUTH = 400 * 1024 * 1024
MAX_CONTENT_LENGTH_FOR_UNAUTH = 100 * 1024 * 1024
PATH_TO_FILES = 'files'

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///info_users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///info_writers.db'
app.config.from_object(Config())
db.app = app
db.init_app(app)
db.create_all()

mail = Mail(app)

serializer = URLSafeSerializer(app.config['SECRET_KEY'])

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@app.errorhandler(404)
def not_found(e):
    flash(e, category='danger')
    return render_template('not_found.html', title='Ooops...')


@app.before_request
def before_request():
    check_operation_id()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('main.html', title='Серебряный век')


@app.route('/info/')
def inf_about():
    return render_template('info.html', title='Серебряный век')


@app.route('/info/<writer>')
def inf_writer(writer):
    D_writer = D_writers.query.get(writer)
    name = D_writer.name
    age = D_writer.age
    info = D_writer.info
    work = D_writer.work
    genre = D_writer.genre
    opinion = D_writer.opinion
    img = '/static/img/' + str(D_writer.image)

    return render_template('info_writer.html', title='ФИО', W_name=name, W_age=age, W_info=info, W_work=work, W_genre=genre, W_opinion=opinion, W_img=img)



@app.route('/gallery/')
def gallery():
    return render_template('gallery.html', title='Серебряный век')


@app.route('/confirmation/<token>')
def confirmation(token):
    email = serializer.loads(token, salt='token_email')
    user = User.query.filter_by(email=email).first()
    if user is not None:
        user.confirmed = True
        update_session()
        flash('Аккаунт успешно создан!', category='success')
        return redirect(url_for('login'))
    else:
        flash('Кажется, ошибка. Попробуйте еще раз')
        return redirect(url_for('registration'))


def check_operation_id():
    session['user_operation_id'] = uuid.uuid4().hex if session.get('user_operation_id') is None \
        else session.get('user_operation_id')



if __name__ == '__main__':
    app.run(port=8080, host='localhost')
