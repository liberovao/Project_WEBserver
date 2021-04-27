
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template
from config import Config
from db import db, D_writers

app = Flask(__name__, template_folder="templates" )
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///info_writers.db'
app.config.from_object(Config())
db.app = app
db.init_app(app)
db.create_all()




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

if __name__ == '__main__':
    app.run(host='localhost', port='8080')
