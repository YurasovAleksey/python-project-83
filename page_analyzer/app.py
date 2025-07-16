from flask import Flask, render_template, request, redirect, url_for, flash, abort
from .url_repository import UrlRepository
import psycopg2
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

def get_db_connection():
    return psycopg2.connect(
        os.getenv('DATABASE_URL'),
        cursor_factory=NamedTupleCursor
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['GET'])
def urls():
    conn = get_db_connection()
    repo = UrlRepository(conn)
    urls_list = repo.get_all_urls()
    conn.close()
    return render_template('urls.html', urls=urls_list)

@app.route('/urls', methods=['POST'])
def add_url():
    raw_url = request.form.get('url')
    if not raw_url:
        flash('URL обязателен', 'danger')
        return render_template('index.html'), 422

    conn = get_db_connection()
    try:
        repo = UrlRepository(conn)
        is_added, url_id, message = repo.add_url(raw_url)  # Переименовал id в url_id
        
        if not url_id:  # Если url_id None (при ошибке)
            flash(message, 'danger')
            return render_template('index.html'), 422
            
        if is_added:
            flash(message, 'success')
        else:
            flash(message, 'info')
            
        return redirect(url_for('show_url', id=url_id))  # Используем url_id
        
    except Exception as e:
        flash(f"Произошла ошибка: {str(e)}", 'danger')
        return render_template('index.html'), 500
        
    finally:
        conn.close()

@app.route('/urls/<int:id>')
def show_url(id):
    conn = get_db_connection()
    repo = UrlRepository(conn)
    url = repo.find_by_id(id)
    conn.close()

    if not url:
        abort(404)
    return render_template('url.html', url=url)

@app.errorhandler(404)
def page_not_found(error):
    return render_template(
        'page_not_found.html'
    ), 404
