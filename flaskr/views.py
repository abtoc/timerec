from flask         import request, redirect, url_for, render_template, flash
from flaskr        import app,db
from flaskr.models import Person

@app.route('/')
def index():
    persons = Person.query.filter_by(enabled=True).all()
    return render_template('index.pug', persons=persons)
    #return redirect(url_for('persons.index'))

from flaskr  import views_persons
app.register_blueprint(views_persons.bp)
from flaskr  import views_workrecs
app.register_blueprint(views_workrecs.bp)
from flaskr  import api_idm
app.register_blueprint(api_idm.bp)
