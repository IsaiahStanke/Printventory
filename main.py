from flask import render_template
from __init__ import create_app

app = create_app()

@app.route('/')
def index():
    return render_template('login.html')

if __name__ == '__main__':
    print("🌍 Running Flask App...")
    app.run(debug=True)
