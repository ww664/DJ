from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='operator')

class InspectionTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)

class InspectionUnit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('inspection_template.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    items = db.relationship('InspectionItem', backref='unit', lazy='dynamic')

class InspectionItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('inspection_unit.id'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    device_name = db.Column(db.String(128), nullable=False)
    part = db.Column(db.String(128), nullable=False)
    content = db.Column(db.String(256), nullable=False)
    standard = db.Column(db.String(256), nullable=True)

class InspectionRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('inspection_template.id'), nullable=False)
    unit_name = db.Column(db.String(128), nullable=False)
    device_name = db.Column(db.String(128), nullable=False)
    part = db.Column(db.String(128), nullable=False)
    content = db.Column(db.String(256), nullable=False)
    standard = db.Column(db.String(256), nullable=True)
    result = db.Column(db.String(64), nullable=False)
    note = db.Column(db.String(256), nullable=True)
    inspected_by = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_custom = db.Column(db.Boolean, default=False)

class OperationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    action = db.Column(db.String(256), nullable=False)
    details = db.Column(db.String(256), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)