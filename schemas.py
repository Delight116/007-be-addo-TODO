from marshmallow import ValidationError
from marshmallow import fields, validate, validates
from marshmallow_peewee import ModelSchema
from models import User, Tasks, Projects
from marshmallow_peewee import Related


class UserSchema(ModelSchema):
    name = fields.Str(validate=[validate.Length(min=3, max=50)])
    password = fields.Str(validate=[validate.Length(min=3, max=30)])

    class Meta:
        model = User

class ProjectsSchema(ModelSchema):
    name = fields.Str(validate=[validate.Length(min=3, max=50)])
    color = fields.Str(validate=[validate.Length(min=3, max=30)])
    to_user = Related(nested=UserSchema)

    class Meta:
        model = Projects

    @validates('to_user')
    def validate_user(self, value):
        if not User.filter(User.id == value).exists():
            raise ValidationError("Can't find User!")

class TasksSchema(ModelSchema):
    name = fields.Str(validate=[validate.Length(min=3, max=100)])
    text = fields.Str(validate=[validate.Length(max=256)])
    date = fields.Str(validate=[validate.Regexp(regex='(\d{4})[/.-](\d{2})[/.-](\d{2})$')])
    status = fields.Bool(default=False)
    priority = fields.Int(default=1, validate=[validate.Range(max=3,min=1)])
    to_project = Related(nested=ProjectsSchema)
    to_user = Related(nested=UserSchema)


    class Meta:
        model = Tasks


    @validates('to_project')
    def validate_to_project(self, value):
        if not Projects.filter(Projects.id == value).exists():
            raise ValidationError("Can't find Project!")

    @validates('to_user')
    def validate_user(self, value):
        if not User.filter(User.id == value).exists():
            raise ValidationError("Can't find User!")



user_schema = UserSchema()
project_schema = ProjectsSchema()
task_schema = TasksSchema()