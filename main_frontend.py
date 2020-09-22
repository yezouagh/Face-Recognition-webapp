from flask import render_template, redirect, Response
from flask_login import login_required, logout_user, current_user
from face_reco import VideoCamera

# Import all the things
from setup_app import app
from service_calls.call_user_service import user_api


app.register_blueprint(user_api)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.route("/")
def home():
    variables = dict(is_authenticated=current_user.is_authenticated)
    return render_template('index.html', **variables)


def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/login_page")
def login_page():
    if current_user.is_authenticated:
        return redirect('/dashboard', code=302)
    return render_template('login_page.html')


@app.route("/dashboard")
@login_required
def dashboard():
    variables = dict(name=current_user.name)

    return render_template('dashboard.html', **variables)


@app.route("/tos")
def terms_of_service():
    variables = dict(is_authenticated=current_user.is_authenticated)
    return render_template('terms_of_service.html', **variables)


@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        current_user.is_authenticated = False
        logout_user()
    return redirect('/', code=302)


@app.errorhandler(401)
def not_logged_in(e):
    variables = dict(message='Please login first')

    return render_template('login_page.html', **variables)


@app.errorhandler(404)
def not_found(e):
    variables = dict(is_authenticated=current_user.is_authenticated,
                     message='404 Page non trouvée',
                     stacktrace=str(e))

    return render_template('error.html', **variables)


if __name__ == '__main__':
    app.run(host='localhost', port=app.config['BASE_PORT'])
