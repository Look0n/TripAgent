from flask import Flask, render_template

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)


@app.route("/")
def accommodation_page():
    return render_template(
        "accommodation.html"
    )


@app.route("/details/<int:accommodation_id>")
def accommodation_detail(accommodation_id):
    return render_template(
        "accommodation_detail.html",
        accommodation_id=accommodation_id
    )


@app.route("/admin/add")
def accommodation_add():
    return render_template(
        "accommodation_add.html"
    )


@app.route("/admin/edit/<int:accommodation_id>")
def accommodation_edit(accommodation_id):
    return render_template(
        "accommodation_edit.html",
        accommodation_id=accommodation_id
    )


@app.route("/health")
def health():
    return {
        "status": "ok",
        "service": "accommodation-frontend"
    }, 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3002,
        debug=False,
        use_reloader=False
    )