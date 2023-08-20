import datetime
import sys

import pytz
from flask_login import UserMixin
from sqlalchemy import event, CheckConstraint

sys.path.append("..")
from const import UserGroup
from db import db


class TimestampMixin():
    # Ref: https://myapollo.com.tw/zh-tw/sqlalchemy-mixin-and-custom-base-classes/
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.datetime.now(pytz.UTC)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        onupdate=lambda: datetime.datetime.now(pytz.UTC)
    )


class User(TimestampMixin, UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    sub = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    group = db.relationship("Group", back_populates='users')

    refresh_token = db.relationship(
        'RefreshToken',
        back_populates='user',
        uselist=False,  # For one-to-one relationship, ref: https://tinyurl.com/jemrw6uf
        cascade='all, delete-orphan',
        passive_deletes=True,
    )
    access_tokens = db.relationship(
        'AccessToken',
        back_populates='user',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    device_features = db.relationship(
        'DeviceFeature',
        back_populates='user',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    device_parameters = db.relationship(
        'DeviceParameter',
        back_populates='user',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    @property
    def is_administrator(self):
        return self.group.name == UserGroup.Administrator


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    users = db.relationship('User', cascade='all, delete', back_populates='group')


# init values in UserGroup after the table just created
# see def of UserGroup for more details
# you can remove this if you use the fixtures or something else to init
@event.listens_for(Group.__table__, 'after_create')
def create_groups(*args, **kwargs):
    for group in UserGroup:
        db.session.add(Group(name=group.value))
    db.session.flush()
    db.session.commit()


class RefreshToken(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    user = db.relationship('User', back_populates='refresh_token')
    access_tokens = db.relationship(
        'AccessToken',
        back_populates='refresh_token',
        cascade='all, delete-orphan',
        passive_deletes=True
    )


class AccessToken(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text)
    expires_at = db.Column(db.DateTime())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    refresh_token_id = db.Column(db.Integer, db.ForeignKey('refresh_token.id'))

    user = db.relationship('User', back_populates='access_tokens')
    refresh_token = db.relationship('RefreshToken', back_populates='access_tokens')

class DeviceFeature(TimestampMixin, db.Model):
    __tablename__ = 'DeviceFeature'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    df_name = db.Column(db.String(255), nullable=False)
    df_type = db.Column(db.String(20), nullable=False)
    param_num = db.Column(db.Integer, nullable=False, default=0)
    content = db.Column(db.Text)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', back_populates='device_features')
    
    __table_args__ = (
        CheckConstraint(df_type.in_(['idf', 'odf']), name='valid_dftype'),
    )
    
    dm_df = db.relationship(
        'DM_DF',
        back_populates='deviceFeature',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

class DeviceModel(TimestampMixin, db.Model):
    __tablename__ = 'DeviceModel'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    dm_name = db.Column(db.String(255), nullable=False, unique=True)
    dm_type = db.Column(db.String(20), nullbale=False)
    plural = db.Column(db.Boolean, nullable=False, default=False) #If true, select DF number using the drop-down menu on GUI.
    device_only = db.Column(db.Boolean, nullable=False, default=False) #If true, select the register device instead of device featrue.
    
    __table_args__ = (
        CheckConstraint(dm_type.in_(['smartphone', 'wearable', 'other']), name='valid_dmtype'),
    )
    
    dm_df = db.relationship(
        'DM_DF',
        back_populates='deviceModel',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    
class DM_DF(TimestampMixin, db.Model):
    __tablename__ = 'DeviceFeatureAndModel'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    
    dm_id = db.Column(db.Integer, db.ForeignKey('deviceModel.id'), nullable=False)
    df_id = db.Column(db.Integer, db.ForeignKey('deviceFeature.id'), nullable=False)
    
    deviceFeature = db.relationship('DeviceFeature', back_populates='dm_df')
    deviceModel = db.relationship('DeviceModel', back_populates='dm_df')
    
class DeviceParameter(TimestampMixin, db.Model):
    __tablename__ = 'DeviceParameter'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    param_type = db.Column(db.String(20), nullable=False)
    min = db.Column(db.Float, nullable=False, default=0)
    max = db.Column(db.Float, nullable=False, default=0)
    idf_type = db.Column(db.String(20), nullable=False, default='sample')
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    df_id = db.Column(db.Integer, db.ForeignKey('deviceFeature.id'), nullable=False)
    dmdf_id = db.Column(db.Integer, db.ForeignKey('dm_df.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False, default=0)
    fn_id = db.Column(db.Integer, db.ForeignKey('function.id'), nullable=True)
    
    # Do not know why it exists.
    normalization = db.Column(db.Boolean, nullable=False, default=0)
    
    user = db.relationship('User', back_populates='device_parameters')
    deviceFeature = db.relationship('DeviceFeature', back_populates='device_parameters')
    dm_df = db.relationship('DM_DF', back_populates='device_parameters')
    unit = db.relationship('Unit', back_populates='device_parameters')
    
    __table_args__ = (
        CheckConstraint(param_type.in_(['int', 'float', 'boolean', 'void', 'string', 'json']), name='valid_paramtype'),
        CheckConstraint(idf_type.in_(['sample', 'variant']))
    )

class Unit(db.Model):
    __tablename__ = 'Unit'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    unit_name = db.Column(db.String(255), nullable=False, unique=True)
    
    device_parameters = db.relationship(
        'DeviceParameter',
        back_populates='unit',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
