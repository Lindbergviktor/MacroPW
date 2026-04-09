from flask import Flask, render_template 

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/meals")
def meals():
    return render_template("meals.html")

@app.route("/statistics")
def statistics():
    return render_template("statistics.html")

@app.route("/workouts")
def workouts():
    return render_template("workouts.html")


if __name__ == "__main__":
    app.run(debug=True)

