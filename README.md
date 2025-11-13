📂 Overview

This Task Manager application allows users to manage daily tasks efficiently through a lightweight Python backend and a clean frontend built using HTML, CSS, and JavaScript. It supports essential task operations like adding, editing, deleting, sorting, and filtering. Data is stored persistently using either JSON or SQLite depending on configuration.

✨ Features

Add, edit, delete tasks (CRUD functionality)

Task attributes:

Title

Description

Priority

Due Date

Status (Pending/Completed)

Tags/Categories

Search and filter functionality

Sorting by priority or due date

Persistent storage (JSON/SQLite)

Simple and responsive UI

🛠️ Tech Stack

Backend: Python (Flask/Streamlit or custom script depending on app.py)

Frontend: HTML, CSS, JavaScript

Database: JSON or SQLite

Environment: pip, virtual environment

📁 Project Structure
task-manager/  
│  
├── app.py                # Backend application  
├── requirements.txt      # Python dependencies  
├── index.html            # Main UI page  
├── *.html                # Additional HTML pages  
├── static/  
│   ├── css/              # Stylesheets  
│   └── js/               # JavaScript files  
└── README.md  

⚙️ Installation
1. Clone or extract the project
git clone <repo-url>
cd task-manager

2. Create a virtual environment

Windows

python -m venv venv
venv\Scripts\activate


macOS/Linux

python3 -m venv venv
source venv/bin/activate

3. Install dependencies
pip install -r requirements.txt

▶️ Running the App
If using Flask
export FLASK_APP=app.py        # macOS/Linux
set FLASK_APP=app.py           # Windows
flask run


or

python app.py

If using Streamlit
streamlit run app.py

Access the app
http://localhost:5000          # Flask
http://localhost:8501          # Streamlit

📘 Usage

Add a task: Fill in the task form and click Add Task.

Edit a task: Click the edit icon on any task.

Delete a task: Click the delete icon.

Search & Filter: Use search bar and filters for quick navigation.

Sort: Sort tasks by due date or priority.

⚙️ Configuration

Modify database paths inside app.py

Update styles/scripts inside /static

Add or edit HTML layouts in root folder or template folder

🧪 Testing (Optional)

To add tests:

pip install pytest
pytest

🚀 Deployment
Using Gunicorn (Flask)
pip install gunicorn
gunicorn -w 4 app:app -b 0.0.0.0:8000

Using Docker
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
