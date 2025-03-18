from flask import render_template
from __init__ import create_app  # Import from the same directory

app = create_app()

@app.route('/')
def index():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
