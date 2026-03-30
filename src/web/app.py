from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def main() -> str:
    return render_template("index.html")


@app.route('/about')
def about() -> str:
    return render_template("about.html")


if __name__ == '__main__':
    app.run(debug=True)
