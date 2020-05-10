import os
import uuid

from flask import Flask, render_template, redirect, flash, url_for, session, send_from_directory, request
from flask_apscheduler import APScheduler
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeSerializer

from db import db, User, update_session
from loginform import LoginForm
from regform import RegForm
from config import Config


MAX_CONTENT_LENGTH_FOR_AUTH = 400 * 1024 * 1024
MAX_CONTENT_LENGTH_FOR_UNAUTH = 100 * 1024 * 1024
PATH_TO_FILES = 'files'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///info_users.db'
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
    return render_template('main.html', title='Автоcервис в Москве')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('Пользователь не найден', category='danger')
            return redirect(url_for('registration'))
        elif user.check_password(form.password.data) is False:
            flash('Неверное имя пользователя или пароль', category='danger')
            return redirect(url_for('login'))
        elif not user.confirmed:
            flash('Пожалуйста, проверьте вашу почту', category='danger')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash('Вход выполнен успешно', category='success')
            return redirect(url_for('index'))
    for errors in form.errors.values():
        for error in errors:
            flash(error, category='danger')
    return render_template('login.html', form=form, title='Авторизация')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# noinspection PyArgumentList
@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        flash('Вы уже числитесь нашим пользователем!', category='danger')
        return redirect(url_for('index'))
    form = RegForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first() is not None:
            flash('Имя пользователя занято', category='danger')
            return redirect(url_for('registration'))
        elif User.query.filter_by(email=form.email.data).first() is not None:
            flash('Такая почта уже используется', category='danger')
            return redirect(url_for('registration'))
        email = form.email.data
        confirmation_token = serializer.dumps(email, salt='token_email')
        user = User(username=form.username.data, email=form.email.data, status='user', confirmed=False)
        user.set_password(form.password.data)
        update_session(user)
        msg = Message('Подтвердите вашу регистрацию', sender='liberovao@yandex.ru',
                      recipients=[email])
        link = url_for('confirmation', token=confirmation_token, _external=True)
        msg.body = 'Перейдите по этой ссылке: {}'.format(link)
        mail.send(msg)
        flash('Пожалуйста, подтвердите вашу почту', category='primary')
        return redirect(url_for('login'))
    for errors in form.errors.values():
        for error in errors:
            flash(error, category='danger')
    return render_template('registration.html', form=form, title='Регистрация')


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
    app.run(port=8080, host='127.0.0.1')
