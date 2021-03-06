from flask         import Blueprint
from flask         import request, jsonify
from flaskr        import db
from flaskr.models import Person, WorkRec
from flaskr.workrule import *
from datetime      import datetime
import json

bp = Blueprint('api_idm', __name__, url_prefix="/api/idm")

def get_work_in(hhmm, staff):
    if staff:
        work_rules = work_rules_staff
    else:
        work_rules = work_rules_staff_no
    for i in work_rules:
        if (i['work_in']) and (i['start_time'] <= hhmm) and (hhmm < i['end_time']):
            return i
    return None

def get_work_out(hhmm, staff):
    if staff:
        work_rules = work_rules_staff
    else:
        work_rules = work_rules_staff_no
    for i in work_rules:
        if (i['work_out']) and (i['start_time'] <= hhmm) and (hhmm < i['end_time']):
            return i
    return None

@bp.route('/<idm>',methods=['GET'])
def get_idm(idm):
    person = Person.query.filter_by(idm=idm).first()
    if person == None:
        return jsonify({"name": "該当者無し"}), 404
    result = dict(
        name=person.name
    )
    return jsonify(result), 200

@bp.route('/<idm>',methods=['POST'])
def post_idm(idm):
    person = Person.query.filter_by(idm=idm).first()
    if person == None:
        return jsonify({"message": "Not Found!"}), 404
    now=datetime.now()
    yymm=now.strftime('%Y%m')
    dd=now.day
    hhmm=now.strftime('%H:%M')
    workrec=WorkRec.query.filter_by(
        person_id=person.id, yymm=yymm, dd=dd
    ).first()
    creation=False
    if workrec == None:
        creation = True
        work_in = get_work_in(hhmm, person.staff)
        #workrec = WorkRec(person_id=person.id, yymm=yymm,dd=dd, work_in=work_in['caption'])
        workrec = WorkRec(person_id=person.id, yymm=yymm,dd=dd, work_in=hhmm)
    else:
        work_in  = get_work_in(workrec.work_in, person.staff)
        work_out = get_work_out(hhmm, person.staff)
        value    = work_out['value'] - work_in['value']
        if (work_in['value'] < 12.0) and (work_out['value'] > 13.0):
            value = value - 1
        workrec.work_out = hhmm
        workrec.value    = value

    db.session.add(workrec)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({}), 500
    if creation:
        result = dict(
            work_in  = workrec.work_in,
            work_out = '--:--'
        )
        return jsonify(result), 201
    result = dict(
        work_in  = workrec.work_in,
        work_out = workrec.work_out
    )
    return jsonify(result), 200