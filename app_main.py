from flask import Flask, Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('login.html')

if __name__ == '__main__':
    app = Flask(__name__)
    app.register_blueprint(main)
    app.run(debug=True, host='0.0.0.0')