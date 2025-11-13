from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import redis
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def user_exists(username):
    return r.exists(f"user:{username}")

def create_user(username, password):
    hashed_pw = generate_password_hash(password)
    r.hset(f"user:{username}", mapping={'password': hashed_pw, 'theme': 'light'})

def validate_user(username, password):
    if not user_exists(username):
        return False
    stored_hash = r.hget(f"user:{username}", "password")
    return check_password_hash(stored_hash, password)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_tasks(username=None, search=None, status=None, priority=None):
    if not username:
        username = session.get('username')
    keys = r.keys(f"task:{username}:*")
    task_keys = [k for k in keys if k.split(":")[-1].isdigit()]
    tasks = []

    for key in task_keys:
        task = r.hgetall(key)
        task['id'] = key.split(":")[-1]
        subtasks = r.lrange(f'{key}:subtasks', 0, -1)
        comments = r.lrange(f'{key}:comments', 0, -1)
        if subtasks:
            task['subtasks'] = subtasks
        if comments:
            task['comments'] = comments

        if search and search.lower() not in (task.get('title','').lower() + task.get('description','').lower()):
            continue
        if status and status != task.get('status'):
            continue
        if priority and priority != task.get('priority'):
            continue
        tasks.append(task)


    tasks.sort(key=lambda t: int(t.get('order', t['id'])))
    return tasks

def get_task(username, task_id):
    key = f'task:{username}:{task_id}'
    if not r.exists(key):
        return None
    task = r.hgetall(key)
    task['id'] = task_id
    task['subtasks'] = r.lrange(f'{key}:subtasks', 0, -1)
    task['comments'] = r.lrange(f'{key}:comments', 0, -1)
    task['history'] = r.lrange(f'{key}:history', 0, -1)
    return task

@app.route('/')
@login_required
def index():
    username = session['username']
    search = request.args.get('search')
    status = request.args.get('status')
    priority = request.args.get('priority')
    tasks = get_tasks(search=search, status=status, priority=priority)
    theme = r.hget(f"user:{username}", "theme") or "light"
    return render_template('index.html', tasks=tasks, theme=theme)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        username = session['username']
        task_id = r.incr(f'task_id:{username}')
        title = request.form['title']
        desc = request.form['description']
        due_date = request.form.get('due_date', '')
        status = request.form.get('status', 'pending')
        priority = request.form.get('priority', 'Medium')
        tags = request.form.get('tags', '')

        r.hset(f'task:{username}:{task_id}', mapping={
            'title': title,
            'description': desc,
            'due_date': due_date,
            'status': status,
            'priority': priority,
            'tags': tags,
            'order': task_id 
        })

        subtasks = request.form.getlist('subtasks')
        for sub in subtasks:
            if sub.strip():
                r.rpush(f'task:{username}:{task_id}:subtasks', sub.strip())

        r.rpush(f'task:{username}:{task_id}:history', f"{datetime.datetime.now()}: Created by {username}")
        flash('Task added successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('add_task.html')

@app.route('/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_task(id):
    username = session['username']
    key = f'task:{username}:{id}'
    if not r.exists(key):
        flash('Task not found.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['description']
        due_date = request.form.get('due_date', '')
        status = request.form.get('status', 'pending')
        priority = request.form.get('priority', 'Medium')
        tags = request.form.get('tags', '')

        r.hset(key, mapping={
            'title': title,
            'description': desc,
            'due_date': due_date,
            'status': status,
            'priority': priority,
            'tags': tags
        })
        r.delete(f'{key}:subtasks')
        subtasks = request.form.getlist('subtasks')
        for sub in subtasks:
            if sub.strip():
                r.rpush(f'{key}:subtasks', sub.strip())
        r.rpush(f'{key}:history', f"{datetime.datetime.now()}: Edited by {username}")
        flash('Task updated successfully.', 'success')
        return redirect(url_for('index'))

    task = get_task(username, id)
    return render_template('edit_task.html', task=task, id=id)

@app.route('/delete/<id>')
@login_required
def delete_task(id):
    username = session['username']
    key = f'task:{username}:{id}'
    r.delete(key)
    r.delete(f'{key}:subtasks')
    r.delete(f'{key}:comments')
    r.delete(f'{key}:history')
    flash('Task deleted.', 'info')
    return redirect(url_for('index'))

@app.route('/task/<id>', methods=['GET', 'POST'])
@login_required
def view_task(id):
    username = session['username']
    task = get_task(username, id)
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        comment = request.form.get('comment')
        if comment:
            r.rpush(f'task:{username}:{id}:comments', f"{username}: {comment}")
            r.rpush(f'task:{username}:{id}:history', f"{datetime.datetime.now()}: Commented by {username}")
            flash('Comment added.', 'success')
            return redirect(url_for('view_task', id=id))
    return render_template('view_task.html', task=task)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password']
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('register'))
        if user_exists(username):
            flash('Username already exists.', 'warning')
            return redirect(url_for('register'))
        create_user(username, password)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password']
        if validate_user(username, password):
            session['username'] = username
            flash(f'Welcome, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/all_tasks')
@login_required
def all_tasks():
    if session['username'] != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    users = [key.split(':')[1] for key in r.keys('user:*')]
    all_tasks = []
    for user in users:
        user_tasks = get_tasks(user)
        for t in user_tasks:
            t['user'] = user
            all_tasks.append(t)
    return render_template('index.html', tasks=all_tasks, all_view=True)

@app.route('/api/search')
@login_required
def api_search():
    query = request.args.get('q', '')
    results = get_tasks(search=query)
    return jsonify(results)

@app.route('/api/reorder', methods=['POST'])
@login_required
def api_reorder():
    username = session['username']
    data = request.get_json()
    order = data.get('order', [])
    for idx, task_id in enumerate(order):
        key = f'task:{username}:{task_id}'
        if r.exists(key):
            r.hset(key, 'order', idx)
    return jsonify({'success': True})

@app.route('/api/bulk_action', methods=['POST'])
@login_required
def api_bulk_action():
    username = session['username']
    data = request.get_json()
    ids = data.get('ids', [])
    action = data.get('action', '')
    updated = []
    for task_id in ids:
        key = f'task:{username}:{task_id}'
        if not r.exists(key):
            continue
        if action == 'delete':
            r.delete(key)
            r.delete(f'{key}:subtasks')
            r.delete(f'{key}:comments')
            r.delete(f'{key}:history')
        elif action == 'complete':
            r.hset(key, 'status', 'completed')
        elif action == 'pending':
            r.hset(key, 'status', 'pending')
        updated.append(task_id)
    return jsonify({'success': True, 'updated': updated})


@app.route('/toggle_theme', methods=['POST'])
@login_required
def toggle_theme():
    """Toggle the user's theme between 'light' and 'dark' in Redis."""
    username = session['username']
    current = r.hget(f"user:{username}", "theme") or "light"
    new_theme = "dark" if current == "light" else "light"
    r.hset(f"user:{username}", "theme", new_theme)
    return jsonify({'theme': new_theme})


if __name__ == '__main__':
    app.run(debug=True)
