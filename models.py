import peewee as pw
import datetime
from playhouse.fields import PasswordField

database = pw.SqliteDatabase("TODO.db")


class BaseModel(pw.Model):
    class Meta:
        database = database


class User(BaseModel):
    name = pw.CharField(unique=True, max_length=30, null=False)
    password = PasswordField()
    state = pw.BooleanField(default=True)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.state

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % (self.name)


class Projects(BaseModel):
    name = pw.CharField(null=False)
    color = pw.CharField(null=False)
    to_user = pw.ForeignKeyField(User, null=False)


class Tasks(BaseModel):
    name = pw.CharField(null=False)
    text = pw.TextField(null=True)
    date = pw.DateTimeField(null=False, default=datetime.datetime.now().strftime("%d-%m-%Y"))
    status = pw.BooleanField(null=True, default=False)
    priority = pw.IntegerField(default=0, null=False)
    to_project = pw.ForeignKeyField(Projects, null=False, related_name="create_in")
    to_user = pw.ForeignKeyField(User, null=False, related_name="create_by")


def initialize():
    User.create_table(fail_silently=True)
    Projects.create_table(fail_silently=True)
    Tasks.create_table(fail_silently=True)
    try:
        User.create(
            name='root',
            password='root'
        )
    except pw.IntegrityError:
        pass
