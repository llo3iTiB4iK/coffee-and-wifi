from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, func
from wtforms import StringField, URLField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.secret_key = "TOP_SECRET_KEY"
Bootstrap5(app)
API_KEY = "TopSecretAPIKey"


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()


# Cafe Add Form Configuration
class CafeForm(FlaskForm):
    name = StringField("Cafe Name", validators=[DataRequired()])
    map_url = URLField("Link for Cafe on Google Maps", validators=[DataRequired()])
    img_url = URLField("Link for Cafe Image", validators=[DataRequired()])
    location = StringField("Cafe Location", validators=[DataRequired()])
    has_sockets = BooleanField("Cafe has sockets")
    has_toilet = BooleanField("Cafe has toilet")
    has_wifi = BooleanField("Cafe has Wi-Fi")
    can_take_calls = BooleanField("Cafe can take calls")
    seats = SelectField("How much seats does cafe have?", choices=['0-10', '10-20', '20-30', '30-40', '40-50', '50+'], validators=[DataRequired()])
    coffee_price = StringField("How much does coffee in this cafe cost?", validators=[DataRequired()])
    submit = SubmitField("Save Cafe!")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/cafe/")
def cafes():
    if request.args.get("cafe_added"):
        header_text = "New Cafe Was Successfully Added"
    elif request.args.get("cafe_deleted"):
        header_text = "Cafe Was Successfully Deleted"
    elif request.args.get("access_denied"):
        header_text = "You Are Not Allowed to Edit Cafe List!"
    else:
        header_text = "All Cafes"
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    return render_template("cafes.html", cafes=[cafe.to_dict() for cafe in all_cafes], header_text=header_text)


@app.route("/add_cafe/", methods=["GET", "POST"])
def add_cafe():
    api_key = request.args.get("api-key")
    if api_key != API_KEY:
        return redirect(url_for('cafes', access_denied=True))
    form = CafeForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
            name=form.data.get("name"),
            map_url=form.data.get("map_url"),
            img_url=form.data.get("img_url"),
            location=form.data.get("location"),
            has_sockets=form.data.get("has_sockets"),
            has_toilet=form.data.get("has_toilet"),
            has_wifi=form.data.get("has_wifi"),
            can_take_calls=form.data.get("can_take_calls"),
            seats=form.data.get("seats"),
            coffee_price=form.data.get("coffee_price"),
        )
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for("cafes", cafe_added=True))
    return render_template("add.html", form=form)


@app.route("/search")
def find_a_cafe():
    queried_loc = request.args.get("loc")
    result = db.session.execute(
        db.select(Cafe).where(func.lower(Cafe.location).ilike(f"%{queried_loc.lower()}%"))
    )
    all_cafes = result.scalars().all()
    if all_cafes:
        return render_template("cafes.html", cafes=[cafe.to_dict() for cafe in all_cafes], header_text="Cafes by Your Query")
    else:
        return render_template("cafes.html", cafes=[], header_text="No Cafes Found by Your Query")


@app.route("/report-closed/<int:cafe_id>")
def delete_cafe(cafe_id):
    cafe_to_delete = db.get_or_404(Cafe, cafe_id)
    api_key = request.args.get("api-key")
    if api_key == API_KEY:
        db.session.delete(cafe_to_delete)
        db.session.commit()
        return redirect(url_for('cafes', cafe_deleted=True))
    else:
        return redirect(url_for('cafes', access_denied=True))


if __name__ == '__main__':
    app.run(debug=True)
