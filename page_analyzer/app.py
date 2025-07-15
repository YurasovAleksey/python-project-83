import os
from flask import Flask, render_template, request, redirect, flash, abort
from psycopg2 import connect
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv


app = Flask(__name__)

SECRET_KEY = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
app.config.update(
    SECRET_KEY=SECRET_KEY,
    DATABASE_URL=DATABASE_URL
)

def get_db_connection():
    conn = connect(DATABASE_URL)
    return conn

@app.route('/')
def index():
    return render_template(
        'index.html',
    )

@app.route('/urls', methods=['GET'])
def get_urls():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM urls ORDER BY created_at DESC;')
    urls = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('urls.html', urls=urls)

@app.route('/urls/<int:id>')
def urls_show(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=NamedTupleCursor)

    cur.execute('SELECT * FROM urls WHERE id = %s;', (id,))
    url = cur.fetchone()

    if not url:
        return abort(404)
    
    cur.close()
    conn.close()

    return render_template('url.html', url=url)


@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        'page_not_found.html'
    ), 404