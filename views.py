from flask import g, Flask, jsonify, request, render_template, current_app, make_response, session
from models import initialize, User, Tasks, Projects
from schemas import user_schema, project_schema, task_schema
from flask_jwt import JWT, jwt_required, current_identity
from flask import abort

from flask_login import LoginManager, current_user, login_user, logout_user
from flask_cors import CORS, cross_origin
from datetime import datetime, timedelta
# from decorators.login_require import login_require
from math import ceil

app = Flask(__name__)
app.secret_key = "super key"

app.config['JWT_AUTH_URL_RULE'] = '/authenticate'

CORS(app=app)


def authenticate(username, password):
    user = User.filter(User.name == username).first()
    if user and user.password.check_password(password):
        return user

    return None


def identity(payload):
    user_id = payload['identity']
    try:
        return User.get(id=user_id)
    except User.DoesNotExist:
        return None


jwt = JWT(app, authenticate, identity)


@app.before_request
def before_request():
    g.user = current_identity


# @app.route("/login", methods=['POST'])
# @cross_origin()
# def login():
#     json_data = request.json
#     print(json_data)
#     if not json_data:
#         return jsonify({'message': 'No input data provided'}), 400
#     data, errors = user_schema.load(json_data)
#     if errors:
#         return jsonify({'message':"No input data"})
#
#     name, password = data.name, data.password
#
#     user = User.select().filter(name=name).first()
#     if user is None:
#         return jsonify({'message':'Incorect username'}),418
#     if password != user.password:
#         return jsonify({'message':'Wrong password'}),418
#     login_user(user)
#
#     return jsonify(**session)

@app.route("/logout")
@cross_origin()
@jwt_required()
def logout():
    logout_user()
    return jsonify({'message': 'Is logout! Bye!!!'}), 200


@app.route("/registration", methods=["POST"])
@cross_origin()
def new_user():
    json_data = request.json
    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    data, errors = user_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    name, password = data.name, data.password
    user = User.select().filter(name=name).first()
    if user is None:
        User.create(name=name, password=password)
        return jsonify({"message": "Created new user: {}".format(name)})
    return jsonify({"message": "Can't Created user: {} is alredy exist".format(name)})


# projects

@app.route("/project", methods=["POST"])
@cross_origin()
@jwt_required()
def new_project():
    json_data = request.json
    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    data, errors = project_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    name, color, user = data.name, data.color, g.user.get_id()

    Projects.create(name=name, color=color, to_user=user)
    addedId = Projects.select().where(Projects.to_user == user).count()
    return jsonify({"message": "Created new project: {}".format(name),
                    'add': project_schema.dump(Projects.select().where(Projects.id == addedId), many=True).data})


@app.route("/projects", methods=["GET"])
@cross_origin()
@jwt_required()
def get_projects():
    counts = {}
    today = datetime.today().strftime("%Y-%m-%d")
    proj = Projects.select().where(Projects.to_user == g.user.get_id())
    proj = project_schema.dump(proj, many=True).data
    task = Tasks.select().where(Tasks.to_user == g.user.get_id(), Tasks.status == False, Tasks.date >= today)
    for s in proj:
        temp = {s.get('id'): task.filter(Tasks.to_project == s.get('id')).count()}
        counts.update(temp)

    for s in proj:
        add = {'count': counts.get(s.get('id'))}
        s.update(add)
    return jsonify(proj), 200


@app.route("/project/<int:id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_project(id):
    try:
        project = Projects.select().where(Projects.id == id, Projects.to_user == g.user.get_id())
        return jsonify(project_schema.dump(project, many=True).data), 200
    except Projects.DoesNotExist:
        return jsonify({'message': 'Can not find project'}), 404


@app.route("/project/<int:id>", methods=["PUT"])
@cross_origin()
@jwt_required()
def update_project(id):
    try:
        project = Projects.get(Projects.id == id, Projects.to_user == g.user.get_id())

    except Projects.DoesNotExist:
        return jsonify({'message': 'Can not find project'}), 404
    newProject, errors = project_schema.load(request.json, instance=project)

    if errors:
        return jsonify(errors), 400

    newProject.save()

    return jsonify(project_schema.dump(newProject).data), 201


@app.route("/project/<int:id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_project(id):
    is_exist = Projects.select().where(Projects.id == id, Projects.to_user == g.user.get_id())
    if not is_exist:
        return jsonify({'message': "Can't find project"}), 404

    relation = Tasks.select().join(Projects).where(Projects.id == id).count()
    if relation > 0:
        return jsonify({'messages': 'Deletion is not possible! This project are use in Task', 'status': 'be use'}), 403

    Projects.delete().where(Projects.id == id).execute()
    return jsonify({'message': 'Project id: {} was delete!'.format(id)}), 410


# users

@app.route("/user", methods=["GET"])
@cross_origin()
@jwt_required()
def get_users():
    return jsonify(user_schema.dump(User.select()).data), 200


@app.route("/user/<int:id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_user(id):
    try:
        user = User.get(id=id)
        return jsonify(user_schema.dump(User.select().where(User.id == id)).data), 200
    except User.DoesNotExist:
        return jsonify({'message': 'Can not find user'}), 404


@app.route('/user/<int:id>', methods=["PUT"])
@cross_origin()
@jwt_required()
def update_user(id):
    try:
        user = User.get(id=id)
    except User.DoesNotExist:
        return jsonify({'message': 'Can not find user'}), 404

    newUser, errors = user_schema.load(request.json, instance=user)

    if errors:
        return jsonify(errors), 400

    newUser.save()

    return jsonify(user_schema.dump(newUser).data), 200


@app.route('/user/<int:id>', methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_user(id):
    is__exists = User.select().filter(id=id).exists()

    if not is__exists:
        return jsonify({"message": "Can't find user with id - `{id}`".format(id=id)}), 404

    User.delete().where(User.id == id).execute()
    return jsonify({}), 204


# tasks
@app.route("/task", methods=["POST"])
@cross_origin()
@jwt_required()
def set_task():
    json_data = request.json
    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    data, errors = task_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    name, text, date, status, priority, to_project_id, to_user_id = data.name, data.text, data.date, data.status, data.priority, data.to_project_id, g.user.get_id()
    project = Projects.select().where(Projects.id == to_project_id, Projects.to_user == g.user.get_id()).exists()
    if not project:
        return jsonify({"message": "Can't create task with project created other User!!!"}), 400

    Tasks.create(name=name, text=text, date=date, status=int(status), priority=int(priority), to_project_id=int(to_project_id), to_user_id=int(to_user_id))
    return jsonify({"message": "Created new task: {}".format(name)}), 201


@app.route("/tasks", methods=["GET"])
@cross_origin()
@jwt_required()
def get_tasks():
    page = request.args.get('page')
    element = request.args.get('onPage')
    print(page, element)
    if not page:
        page = 1
    if not element:
        element = 15
    today = datetime.today().strftime("%Y-%m-%d")
    page = int(page)
    element = int(element)
    count = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == Tasks.to_user == g.user.get_id(), Tasks.status == False, Tasks.date >= today).order_by(Tasks.date, +Tasks.priority).count()
    task = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == Tasks.to_user == g.user.get_id(), Tasks.status == False, Tasks.date >= today).order_by(Tasks.date, +Tasks.priority)[(page - 1) * element: page * element]
    return jsonify({'data': task_schema.dump(task, many=True).data, 'pageCount': ceil(count / element)}), 200


@app.route("/task/<int:id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_task(id):
    try:
        task = Tasks.select().where(Tasks.id == id, Tasks.to_user == g.user.get_id())
        return jsonify(task_schema.dump(task, many=True).data), 200
    except Tasks.DoesNotExist:
        return jsonify({'message': 'Can not find task'}), 404


@app.route("/tasks/next/<int:days>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_next_tasks(days):
    page = request.args.get('page')
    element = request.args.get('onPage')
    print(page, element)
    if not page:
        page = 1
    if not element:
        element = 15
    page = int(page)
    element = int(element)
    today = datetime.today().strftime("%Y-%m-%d")
    nextDays = (datetime.today() + timedelta(days=days)).strftime("%Y-%m-%d")
    count = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == g.user.get_id(), Tasks.status == False, Tasks.date >= today, Tasks.date < nextDays).order_by(Tasks.date, +Tasks.priority).count()
    task = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == g.user.get_id(), Tasks.status == False, Tasks.date >= today, Tasks.date < nextDays).order_by(Tasks.date, +Tasks.priority)[(page - 1) * element: page * element]
    return jsonify({'data': task_schema.dump(task, many=True).data, 'pageCount': ceil(count / element)}), 200


@app.route("/tasks/today", methods=["GET"])
@cross_origin()
@jwt_required()
def get_today_tasks():
    page = request.args.get('page')
    element = request.args.get('onPage')
    print(page, element)
    if not page:
        page = 1
    if not element:
        element = 15
    page = int(page)
    element = int(element)
    today = datetime.today().strftime("%Y-%m-%d")
    count = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == 2, Tasks.status == False, Tasks.date == today).order_by(Tasks.date, +Tasks.priority).count()
    task = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == 2, Tasks.status == False, Tasks.date == today).order_by(Tasks.date, +Tasks.priority)[(page - 1) * element: page * element]
    return jsonify({'data': task_schema.dump(task, many=True).data, 'pageCount': ceil(count / element)}), 200


@app.route("/tasks/archive", methods=["GET"])
@cross_origin()
@jwt_required()
def get_archeve_tasks():
    page = request.args.get('page')
    element = request.args.get('onPage')
    print(page, element)
    if not page:
        page = 1
    if not element:
        element = 15
    page = int(page)
    element = int(element)
    today = datetime.today().strftime("%Y-%m-%d")
    count = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == g.user.get_id(), Tasks.date < today).order_by(
        Tasks.date, +Tasks.priority).count()
    task = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == g.user.get_id(), Tasks.date < today).order_by(
        Tasks.date, +Tasks.priority)[(page - 1) * element: page * element]

    return jsonify({'data': task_schema.dump(task, many=True).data, 'pageCount': ceil(count / element)}), 200


@app.route('/task/<int:id>', methods=["PUT"])
@cross_origin()
@jwt_required()
def update_task(id):
    try:
        task = Tasks.get(Tasks.id == id)
        # .filter(Tasks.to_user == g.user.get_id())

    except Tasks.DoesNotExist:
        return jsonify({"message": "Can't find task with id - `{id}`".format(id=id)}), 404

    newTask, errors = task_schema.load(request.json, instance=task)
    if errors:
        return jsonify(errors), 400

    # newTask.id = id
    newTask.save()

    return jsonify(project_schema.dump(newTask).data), 200


@app.route('/task/<int:id>', methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_task(id):
    is__exists = Tasks.select().where(Tasks.id == id, Tasks.to_user == g.user.get_id()).exists()

    if not is__exists:
        return jsonify({"message": "Can't find task with id - `{id}`".format(id=id)}), 404

    Tasks.delete().where(Tasks.id == id).execute()
    return jsonify({}), 204


if __name__ == "__main__":
    initialize()
    app.run(debug=True, use_reloader=True)
