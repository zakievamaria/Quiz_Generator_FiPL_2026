from flask import Flask, render_template, url_for

app = Flask(__name__, template_folder=r'C:\Study\flaskProject\templates')

@app.route('/')
def main():
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")



if __name__ == '__main__':
    app.run(debug=True)