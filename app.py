import os
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = "gaon_khiladi_secret_key_change_this"

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(BASE_DIR, "gaon_khiladi.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

VIDEO_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "videos"
)

DOCUMENT_FOLDER = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "documents"
)

os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(DOCUMENT_FOLDER, exist_ok=True)

app.config["VIDEO_FOLDER"] = VIDEO_FOLDER
app.config["DOCUMENT_FOLDER"] = DOCUMENT_FOLDER

ALLOWED_VIDEO_EXTENSIONS = {
    "mp4",
    "mov",
    "avi",
    "mkv",
    "webm"
}

db = SQLAlchemy(app)


# =========================================================
# DATABASE MODELS
# =========================================================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        nullable=False,
        default="athlete"
    )

    full_name = db.Column(db.String(150))

    phone = db.Column(db.String(20))

    city = db.Column(db.String(100))

    state = db.Column(db.String(100))

    language = db.Column(
        db.String(50),
        default="English"
    )

    bio = db.Column(db.Text)

    sport = db.Column(db.String(100))

    age = db.Column(db.Integer)

    gender = db.Column(db.String(30))

    profile_image = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Performance(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    athlete_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    sport = db.Column(
        db.String(100),
        nullable=False
    )

    event = db.Column(db.String(100))

    metric = db.Column(
        db.String(100),
        nullable=False
    )

    value = db.Column(db.Float, nullable=False)

    unit = db.Column(db.String(50))

    benchmark = db.Column(db.Float)

    verified = db.Column(
        db.Boolean,
        default=False
    )

    verified_by = db.Column(db.Integer)

    date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    athlete = db.relationship(
        "User",
        foreign_keys=[athlete_id]
    )


class Video(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    athlete_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    title = db.Column(db.String(200))

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    athlete = db.relationship(
        "User",
        foreign_keys=[athlete_id]
    )


class TrainingPlan(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    sport = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(db.Text)

    duration = db.Column(db.String(100))

    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    coach = db.relationship(
        "User",
        foreign_keys=[coach_id]
    )


class TrainingAssignment(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    plan_id = db.Column(
        db.Integer,
        db.ForeignKey("training_plan.id")
    )

    athlete_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    progress = db.Column(
        db.Integer,
        default=0
    )

    status = db.Column(
        db.String(30),
        default="Assigned"
    )

    plan = db.relationship("TrainingPlan")

    athlete = db.relationship(
        "User",
        foreign_keys=[athlete_id]
    )


class Opportunity(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(200),
        nullable=False
    )

    sport = db.Column(
        db.String(100),
        nullable=False
    )

    age_min = db.Column(db.Integer)

    age_max = db.Column(db.Integer)

    location = db.Column(
        db.String(200),
        nullable=False
    )

    date = db.Column(db.String(50))

    description = db.Column(db.Text)

    organizer = db.Column(db.String(200))

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


class Notification(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(db.Text)

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def allowed_video(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_VIDEO_EXTENSIONS
    )


def current_user():

    if "user_id" not in session:
        return None

    return db.session.get(
        User,
        session["user_id"]
    )


def login_required():

    return "user_id" in session


def create_notification(
    user_id,
    title,
    message
):

    notification = Notification(
        user_id=user_id,
        title=title,
        message=message
    )

    db.session.add(notification)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    athlete_count = User.query.filter_by(
        role="athlete"
    ).count()

    coach_count = User.query.filter_by(
        role="coach"
    ).count()

    opportunity_count = Opportunity.query.count()

    return render_template(
        "home.html",
        athlete_count=athlete_count,
        coach_count=coach_count,
        opportunity_count=opportunity_count
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username"
        ).strip()

        password = request.form.get(
            "password"
        )

        role = request.form.get(
            "role",
            "athlete"
        )

        full_name = request.form.get(
            "full_name"
        )

        sport = request.form.get(
            "sport"
        )

        age = request.form.get(
            "age"
        )

        city = request.form.get(
            "city"
        )

        state = request.form.get(
            "state"
        )

        language = request.form.get(
            "language",
            "English"
        )

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:

            flash(
                "Username already exists.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        hashed_password = generate_password_hash(
            password
        )

        user = User(
            username=username,
            password=hashed_password,
            role=role,
            full_name=full_name,
            sport=sport,
            age=int(age) if age else None,
            city=city,
            state=state,
            language=language
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Registration successful. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "error"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    performances = Performance.query.filter_by(
        athlete_id=user.id
    ).all() if user.role == "athlete" else []

    assignments = TrainingAssignment.query.filter_by(
        athlete_id=user.id
    ).all() if user.role == "athlete" else []

    notifications = Notification.query.filter_by(
        user_id=user.id,
        is_read=False
    ).count()

    return render_template(
        "dashboard.html",
        user=user,
        performances=performances,
        assignments=assignments,
        notifications=notifications
    )


# =========================================================
# ATHLETE PROFILE
# =========================================================

@app.route(
    "/athlete/<int:athlete_id>"
)
def athlete_profile(athlete_id):

    athlete = User.query.get_or_404(
        athlete_id
    )

    performances = Performance.query.filter_by(
        athlete_id=athlete.id
    ).order_by(
        Performance.date.desc()
    ).all()

    videos = Video.query.filter_by(
        athlete_id=athlete.id
    ).order_by(
        Video.uploaded_at.desc()
    ).all()

    return render_template(
        "athlete_profile.html",
        athlete=athlete,
        performances=performances,
        videos=videos
    )


# =========================================================
# EDIT PROFILE
# =========================================================

@app.route(
    "/profile",
    methods=["GET", "POST"]
)
def profile():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if request.method == "POST":

        user.full_name = request.form.get(
            "full_name"
        )

        user.phone = request.form.get(
            "phone"
        )

        user.city = request.form.get(
            "city"
        )

        user.state = request.form.get(
            "state"
        )

        user.bio = request.form.get(
            "bio"
        )

        user.sport = request.form.get(
            "sport"
        )

        age = request.form.get(
            "age"
        )

        user.age = (
            int(age)
            if age
            else None
        )

        user.language = request.form.get(
            "language"
        )

        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    return render_template(
        "profile.html",
        user=user
    )


# =========================================================
# ATHLETE SEARCH / SCOUT DASHBOARD
# =========================================================

@app.route("/athletes")
def athletes():

    if not login_required():

        return redirect(
            url_for("login")
        )

    sport = request.args.get(
        "sport",
        ""
    )

    city = request.args.get(
        "city",
        ""
    )

    min_age = request.args.get(
        "min_age",
        ""
    )

    max_age = request.args.get(
        "max_age",
        ""
    )

    query = User.query.filter_by(
        role="athlete"
    )

    if sport:

        query = query.filter(
            User.sport.ilike(
                f"%{sport}%"
            )
        )

    if city:

        query = query.filter(
            User.city.ilike(
                f"%{city}%"
            )
        )

    if min_age:

        query = query.filter(
            User.age >= int(min_age)
        )

    if max_age:

        query = query.filter(
            User.age <= int(max_age)
        )

    athletes = query.all()

    return render_template(
        "athletes.html",
        athletes=athletes
    )


# =========================================================
# ADD PERFORMANCE
# =========================================================

@app.route(
    "/add-performance",
    methods=["GET", "POST"]
)
def add_performance():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if user.role != "athlete":

        flash(
            "Only athletes can add their performance.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        sport = request.form.get(
            "sport"
        )

        event = request.form.get(
            "event"
        )

        metric = request.form.get(
            "metric"
        )

        value = float(
            request.form.get("value")
        )

        unit = request.form.get(
            "unit"
        )

        benchmark_value = request.form.get(
            "benchmark"
        )

        benchmark = (
            float(benchmark_value)
            if benchmark_value
            else None
        )

        performance = Performance(
            athlete_id=user.id,
            sport=sport,
            event=event,
            metric=metric,
            value=value,
            unit=unit,
            benchmark=benchmark,
            verified=False
        )

        db.session.add(performance)

        # Notify coaches
        coaches = User.query.filter_by(
            role="coach"
        ).all()

        for coach in coaches:

            create_notification(
                coach.id,
                "New Performance Added",
                f"{user.full_name or user.username} "
                f"added a new {sport} performance."
            )

        db.session.commit()

        flash(
            "Performance submitted for verification.",
            "success"
        )

        return redirect(
            url_for(
                "athlete_profile",
                athlete_id=user.id
            )
        )

    return render_template(
        "add_performance.html"
    )


# =========================================================
# VIDEO UPLOAD
# =========================================================

@app.route(
    "/upload-video",
    methods=["POST"]
)
def upload_video():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if user.role != "athlete":

        flash(
            "Only athletes can upload videos.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    video = request.files.get(
        "video"
    )

    title = request.form.get(
        "title"
    )

    if not video or video.filename == "":

        flash(
            "Please select a video.",
            "error"
        )

        return redirect(
            url_for(
                "athlete_profile",
                athlete_id=user.id
            )
        )

    if not allowed_video(
        video.filename
    ):

        flash(
            "Unsupported video format.",
            "error"
        )

        return redirect(
            url_for(
                "athlete_profile",
                athlete_id=user.id
            )
        )

    filename = secure_filename(
        video.filename
    )

    filename = (
        str(user.id)
        + "_"
        + str(int(datetime.utcnow().timestamp()))
        + "_"
        + filename
    )

    path = os.path.join(
        app.config["VIDEO_FOLDER"],
        filename
    )

    video.save(path)

    new_video = Video(
        athlete_id=user.id,
        filename=filename,
        title=title
    )

    db.session.add(new_video)
    db.session.commit()

    flash(
        "Performance video uploaded.",
        "success"
    )

    return redirect(
        url_for(
            "athlete_profile",
            athlete_id=user.id
        )
    )


# =========================================================
# VERIFY PERFORMANCE
# =========================================================

@app.route(
    "/verify-performance/<int:performance_id>"
)
def verify_performance(performance_id):

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if user.role not in [
        "coach",
        "scout",
        "admin"
    ]:

        flash(
            "You do not have permission.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    performance = Performance.query.get_or_404(
        performance_id
    )

    performance.verified = True
    performance.verified_by = user.id

    create_notification(
        performance.athlete_id,
        "Performance Verified",
        f"Your {performance.sport} performance "
        f"({performance.metric}) has been verified."
    )

    db.session.commit()

    flash(
        "Performance verified.",
        "success"
    )

    return redirect(
        url_for(
            "athlete_profile",
            athlete_id=performance.athlete_id
        )
    )


# =========================================================
# OPPORTUNITIES
# =========================================================

@app.route("/opportunities")
def opportunities():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    opportunities = Opportunity.query.order_by(
        Opportunity.id.desc()
    ).all()

    matched = []

    for opportunity in opportunities:

        score = 0

        if user.sport and opportunity.sport:

            if user.sport.lower() == opportunity.sport.lower():

                score += 60

        if user.age:

            if (
                opportunity.age_min
                and opportunity.age_max
                and
                opportunity.age_min
                <= user.age
                <= opportunity.age_max
            ):

                score += 25

        if user.city and opportunity.location:

            if user.city.lower() in opportunity.location.lower():

                score += 15

        matched.append(
            {
                "opportunity": opportunity,
                "score": score
            }
        )

    matched.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return render_template(
        "opportunities.html",
        matched=matched
    )


# =========================================================
# ADD OPPORTUNITY
# =========================================================

@app.route(
    "/add-opportunity",
    methods=["GET", "POST"]
)
def add_opportunity():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if user.role not in [
        "coach",
        "scout",
        "admin"
    ]:

        flash(
            "Only coaches and scouts can add opportunities.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        opportunity = Opportunity(

            title=request.form.get(
                "title"
            ),

            sport=request.form.get(
                "sport"
            ),

            age_min=int(
                request.form.get("age_min")
            ),

            age_max=int(
                request.form.get("age_max")
            ),

            location=request.form.get(
                "location"
            ),

            date=request.form.get(
                "date"
            ),

            description=request.form.get(
                "description"
            ),

            organizer=request.form.get(
                "organizer"
            ),

            created_by=user.id
        )

        db.session.add(opportunity)

        # Notify athletes matching sport
        athletes = User.query.filter_by(
            role="athlete"
        ).all()

        for athlete in athletes:

            if (
                athlete.sport
                and athlete.sport.lower()
                == opportunity.sport.lower()
            ):

                create_notification(
                    athlete.id,
                    "New Trial Opportunity",
                    f"{opportunity.title} is available "
                    f"for {opportunity.sport} athletes."
                )

        db.session.commit()

        flash(
            "Opportunity created successfully.",
            "success"
        )

        return redirect(
            url_for("opportunities")
        )

    return render_template(
        "add_opportunity.html"
    )


# =========================================================
# TRAINING PLANS
# =========================================================

@app.route("/training")
def training():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    plans = TrainingPlan.query.all()

    assignments = []

    if user.role == "athlete":

        assignments = TrainingAssignment.query.filter_by(
            athlete_id=user.id
        ).all()

    return render_template(
        "training.html",
        plans=plans,
        assignments=assignments
    )


# =========================================================
# ADD TRAINING PLAN
# =========================================================

@app.route(
    "/add-training",
    methods=["GET", "POST"]
)
def add_training():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if user.role not in [
        "coach",
        "scout",
        "admin"
    ]:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        plan = TrainingPlan(

            title=request.form.get(
                "title"
            ),

            sport=request.form.get(
                "sport"
            ),

            description=request.form.get(
                "description"
            ),

            duration=request.form.get(
                "duration"
            ),

            coach_id=user.id
        )

        db.session.add(plan)
        db.session.commit()

        flash(
            "Training plan created.",
            "success"
        )

        return redirect(
            url_for("training")
        )

    return render_template(
        "add_training.html"
    )


# =========================================================
# ASSIGN TRAINING PLAN
# =========================================================

@app.route(
    "/assign-training/<int:plan_id>/<int:athlete_id>"
)
def assign_training(plan_id, athlete_id):

    if not login_required():

        return redirect(
            url_for("login")
        )

    user = current_user()

    if user.role not in [
        "coach",
        "scout",
        "admin"
    ]:

        return redirect(
            url_for("dashboard")
        )

    plan = TrainingPlan.query.get_or_404(
        plan_id
    )

    athlete = User.query.get_or_404(
        athlete_id
    )

    existing = TrainingAssignment.query.filter_by(
        plan_id=plan.id,
        athlete_id=athlete.id
    ).first()

    if not existing:

        assignment = TrainingAssignment(
            plan_id=plan.id,
            athlete_id=athlete.id,
            progress=0,
            status="Assigned"
        )

        db.session.add(
            assignment
        )

        create_notification(
            athlete.id,
            "New Training Plan",
            f"You have been assigned: {plan.title}"
        )

        db.session.commit()

    flash(
        "Training plan assigned.",
        "success"
    )

    return redirect(
        url_for("athletes")
    )


# =========================================================
# UPDATE TRAINING PROGRESS
# =========================================================

@app.route(
    "/training-progress/<int:assignment_id>",
    methods=["POST"]
)
def training_progress(assignment_id):

    if not login_required():

        return redirect(
            url_for("login")
        )

    assignment = TrainingAssignment.query.get_or_404(
        assignment_id
    )

    if assignment.athlete_id != session["user_id"]:

        return redirect(
            url_for("dashboard")
        )

    progress = int(
        request.form.get(
            "progress",
            0
        )
    )

    progress = max(
        0,
        min(
            progress,
            100
        )
    )

    assignment.progress = progress

    if progress >= 100:

        assignment.status = "Completed"

    elif progress > 0:

        assignment.status = "In Progress"

    else:

        assignment.status = "Assigned"

    db.session.commit()

    flash(
        "Training progress updated.",
        "success"
    )

    return redirect(
        url_for("training")
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

@app.route("/notifications")
def notifications():

    if not login_required():

        return redirect(
            url_for("login")
        )

    user_notifications = Notification.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Notification.created_at.desc()
    ).all()

    return render_template(
        "notifications.html",
        notifications=user_notifications
    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

with app.app_context():

    db.create_all()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )