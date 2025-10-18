from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ===================== IMAGE UPLOAD CONFIG =====================
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ===================== COMMON DB CONNECTION =====================
def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn


# ===================== USERS DB =====================
def init_user_db():
    conn = get_db_connection('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )''')
    conn.commit()
    conn.close()


# ===================== RECIPE DB =====================
def init_recipe_db():
    conn = get_db_connection('cakes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    ingredients TEXT NOT NULL,
                    recipe TEXT NOT NULL,
                    image TEXT
                )''')
    conn.commit()
    conn.close()


# ===================== REGISTER =====================
@app.route('/', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            flash("⚠️ Please fill in all fields.", "error")
            return redirect(url_for('register'))

        conn = get_db_connection('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone():
            conn.close()
            flash("❌ Username already exists. Please choose another.", "error")
            return redirect(url_for('register'))

        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        flash("✅ Account created successfully! Please login now.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ===================== LOGIN =====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['username'] = username
            flash(f"👋 Welcome back, {username}!", "success")
            return redirect(url_for('index'))
        else:
            flash("❌ Invalid username or password. Please try again.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')


# ===================== LOGOUT =====================
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("👋 You have been logged out successfully.", "info")
    return redirect(url_for('login'))


# ===================== HOME =====================
@app.route('/home')
@app.route('/index')
def index():
    if 'username' not in session:
        flash("⚠️ Please log in to access Cake World.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection('cakes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM recipes")
    data = c.fetchall()
    conn.close()
    return render_template('index.html', recipes=data)


# ===================== ADD RECIPE =====================
@app.route('/add', methods=['GET', 'POST'])
def add():
    if 'username' not in session:
        flash("⚠️ Please log in to add recipes.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        recipe = request.form['recipe']

        image_file = request.files.get('image')
        image_filename = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_filename = filename

        conn = get_db_connection('cakes.db')
        c = conn.cursor()
        c.execute("INSERT INTO recipes (title, ingredients, recipe, image) VALUES (?, ?, ?, ?)",
                  (title, ingredients, recipe, image_filename))
        conn.commit()
        conn.close()
        flash("🎂 Recipe added successfully!", "success")
        return redirect(url_for('index'))

    return render_template('add.html')


# ===================== UPDATE RECIPE =====================
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    conn = get_db_connection('cakes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM recipes WHERE id=?", (id,))
    recipe = c.fetchone()

    if not recipe:
        flash("❌ Recipe not found.", "error")
        conn.close()
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        recipe_text = request.form['recipe']

        image_file = request.files.get('image')
        image_filename = recipe['image']  # default: old image

        # ✅ If user uploads a new image, replace the old one
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_filename = filename

        c.execute("""
            UPDATE recipes 
            SET title=?, ingredients=?, recipe=?, image=? 
            WHERE id=?
        """, (title, ingredients, recipe_text, image_filename, id))

        conn.commit()
        conn.close()

        flash("🍰 Recipe updated successfully!", "success")
        return redirect(url_for('index'))

    conn.close()
    return render_template('update.html', recipe=recipe)



# ===================== DELETE RECIPE =====================
@app.route('/delete/<int:id>')
def delete(id):
    if 'username' not in session:
        flash("⚠️ Please log in to delete recipes.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection('cakes.db')
    c = conn.cursor()
    c.execute("DELETE FROM recipes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("🗑️ Recipe deleted successfully!", "info")
    return redirect(url_for('index'))


# ===================== SEARCH =====================
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        if not keyword:
            flash("⚠️ Please enter a search term.", "warning")
            return redirect(url_for('search'))

        conn = get_db_connection('cakes.db')
        c = conn.cursor()
        # ✅ Search only by title
        c.execute("SELECT * FROM recipes WHERE title LIKE ?", ('%' + keyword + '%',))
        recipes = c.fetchall()
        conn.close()

        return render_template('search.html', recipes=recipes, query=keyword)

    return render_template('search.html', recipes=[], query=None)




# ===================== VIEW RECIPE (PROFESSIONAL PAGE) =====================
@app.route('/view_recipe/<int:id>')
def view_recipe(id):
    conn = get_db_connection('cakes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM recipes WHERE id=?", (id,))
    recipe = c.fetchone()
    conn.close()
    return render_template('view_recipe.html', recipe=recipe)


# ===================== INIT =====================
if __name__ == '__main__':
    init_user_db()
    init_recipe_db()
    app.run(debug=True)
