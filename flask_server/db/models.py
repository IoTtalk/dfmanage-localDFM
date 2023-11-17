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
    __tablename__ = 'user'
    
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
    projects = db.relationship(
        'Project',
        back_populates='user',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    devices = db.relationship(
        'Device',
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
    
    users = db.relationship(
        'User', 
        cascade='all, delete', 
        back_populates='group'
    )


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
    __tablename__ = 'deviceFeature'
    
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
    device_parameters = db.relationship(
        'DeviceParameter',
        back_populates='deviceFeature',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    df_objects = db.relationship(
        'DF_Object',
        back_populates='deviceFeature',
        cascade='all, delete-orphan',
        passive_deletes=True
    )


class DeviceModel(TimestampMixin, db.Model):
    __tablename__ = 'deviceModel'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    dm_name = db.Column(db.String(255), nullable=False, unique=True)
    dm_type = db.Column(db.String(20), nullable=False)
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
    device_objects = db.relationship(
        'DeviceObject',
        back_populates='deviceModel',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    devices = db.relationship(
        'Device',
        back_populates='deviceModel',
        cascade='all, delete-orphan',
        passive_deletes=True
    )


class DM_DF(TimestampMixin, db.Model):
    __tablename__ = 'dm_df'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    
    dm_id = db.Column(db.Integer, db.ForeignKey('deviceModel.id'), nullable=False)
    df_id = db.Column(db.Integer, db.ForeignKey('deviceFeature.id'), nullable=False)
    
    deviceFeature = db.relationship('DeviceFeature', back_populates='dm_df')
    deviceModel = db.relationship('DeviceModel', back_populates='dm_df')
    
    device_parameters = db.relationship(
        'DeviceParameter',
        back_populates='dm_df',
        cascade='all, delete-orphan',
        passive_deletes=True
    )


class DeviceParameter(TimestampMixin, db.Model):
    __tablename__ = 'deviceParameter'
    
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
    function = db.relationship('Function', back_populates='device_parameters')
    
    __table_args__ = (
        CheckConstraint(param_type.in_(['int', 'float', 'boolean', 'void', 'string', 'json']), name='valid_paramtype'),
        CheckConstraint(idf_type.in_(['sample', 'variant']))
    )


class Unit(db.Model):
    __tablename__ = 'unit'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    unit_name = db.Column(db.String(255), nullable=False, unique=True)
    
    device_parameters = db.relationship(
        'DeviceParameter',
        back_populates='unit',
        cascade='all, delete-orphan',
        passive_deletes=True
    )


class Function(db.Model):
    __tablename__ = 'function'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    fn_name = db.Column(db.String(255), nullable=False, unique=True)
    is_protect = db.Column(db.Boolean, nullable=False, default=0)
    
    device_parameters = db.relationship(
        'DeviceParameter',
        back_populates='function',
    )
    df_modules = db.relationship(
        'DF_Module',
        back_populates='function'
    )
    mj_modules = db.relationship(
        'MJ_Module',
        back_populates='function'
    )


class Project(db.Model):
    __tablename__ = 'project'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    p_name = db.Column(db.String(255), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False)
    restart = db.Column(db.Boolean, nullable=False, default=0)
    exception = db.Column(db.Text, nullable=True)
    sim = db.Column(db.String(20), nullable=False, default='off')
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    user = db.relationship('User', back_populates='projects')
    
    __table_args__ = (
        CheckConstraint(status.in_(['on', 'off']), name='valid_status'),
        CheckConstraint(sim.in_(['on', 'off']), name='valid_sim')
    )
    
    device_objects = db.relationship(
        'DeviceObject',
        back_populates='project',
    )
    netApps = db.relationship('NetworkApp', backref='project')
    
    def export(self) -> dict:
        return{
            'NetworkApplication' : [na.export() for na in self.netApps],
            'DeviceObject' : {do.id : do.export() for do in self.device_objects},
            **self.to_dict(('p_name',))
        }


class NetworkApp(db.Model):
    __tablename__ = 'netApps'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    na_name = db.Column(db.String(255), nullable=False)
    idx = db.Column(db.Integer, nullable=False)
    
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    df_modules = db.relationship('DF_Module', backref='netApps')
    mj_modules = db.relationship('MJ_Module', backref='netApps')
    
    def export(self) -> dict:
        return {
            'DF_Module' : [dfm.export() for dfm in self.df_modules],
            'Multiple_Join_Module' : [mjm.export() for mjm in self.mj_modules],
            **self.to_dict(('na_name', 'idx'))
        }


class DF_Module(db.Model):
    __tablename__ = 'DeviceFeatureModule'
    
    param_i = db.Column(db.Integer, primary_key=True, autoincrement=False, nullable=False)
    idf_type = db.Column(db.Enum('sample', 'variant'), nullable=False, default='sample')
    min = db.Column(db.Float, nullable=False, default=0)
    max = db.Column(db.Float, nullable=False, default=0)
    color = db.Column(db.Enum('red', 'black'), nullable=False, default='black')
    
    # Do not know why it exists.
    normalization = db.Column(db.Boolean, nullable=False, default=0)
    
    netApps_id = db.Column(db.Integer, db.ForeignKey('netApps.id'),
                              primary_key=True, autoincrement=False, nullable=False)
    df_object_id = db.Column(db.Integer, db.ForeignKey('df_object.id'),
                             primary_key=True, autoincrement=False, nullable=False)
    function_id = db.Column(db.Integer, db.ForeignKey('function.id'), nullable=True)
    
    df_object = db.relationship('DF_Object', back_populates='df_modules')
    function = db.relationship('Function', back_populates='df_modules')
    
    def export(self) -> dict:
        data = ('df_objects_id',
                'param_i',
                'idf_type',
                'min',
                'max',
                'normalization',
                'function.fn_name'
                )
        return self.to_dick(data)


class DF_Object(db.Model):
    __tablename__ = 'df_object'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    
    df_id = db.Column(db.Integer, db.ForeignKey('deviceFeature.id'), nullable=False)
    do_id = db.Column(db.Integer, db.ForeignKey('deviceObject.id'), nullable=False)
    
    deviceFeature = db.relationship('DeviceFeature', back_populates='df_objects')
    deviceObject = db.relationship('DeviceObject', back_populates='df_objects')
    
    df_modules = db.relationship(
        'DF_Module', 
        back_populates='df_object',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    mj_modules = db.relationship(
        'MJ_Module', 
        back_populates='df_object',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    
    def export(self) -> dict:
        data = ('deviceFeature.df_name', 'name')
        return self.to_dict(data)


class DeviceObject(db.Model):
    __tablename__ = 'deviceObject'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    idx = db.Column(db.Integer, nullable=False, default=0)
    
    dm_id = db.Column(db.Integer, db.ForeignKey('deviceModel.id'), nullable=False)
    p_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    d_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=True)
    
    deviceModel = db.relationship('DeviceModel', back_populates='device_objects')
    project = db.relationship('Project', back_populates='device_objects')
    device = db.relationship('Device', back_populates='device_objects')
    
    df_objects = db.relationship(
        'DF_Object',
        back_populates='deviceObject',
        cascade='all, delete-orphan',
        passive_deletes=True
    )
    
    def export(self) -> dict:
        return {
            'DF_Object' : {dfo.id: dfo.export() for dfo in self.df_objects},
            **self.to_dict(('idx', 'deviceModel.dm_name'))
        }


class Device(db.Model):
    __tablename__ = 'device'
    
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    mac_addr = db.Column(db.String(255), nullable=False, unique=True)
    d_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum('online', 'offline'), nullable=False, default='online')
    monitor = db.Column(db.String(255), nullable=False, default='')
    is_sim = db.Column(db.Boolean, nullable=False, default=0)
    register_time = db.Column(db.DateTime, nullable=False)
    extra_setup_webpage = db.Column(db.String(255), nullable=False, default='')
    device_webpage = db.Column(db.String(255), nullable=False, default='')
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dm_id = db.Column(db.Integer, db.ForeignKey('deviceModel.id'), nullable=False)
    
    user = db.relationship('User', back_populates='devices')
    deviceModel = db.relationship('DeviceModel', back_populates='devices')
    
    device_objects = db.relationship(
        'DeviceObject',
        back_populates='device',
        cascade='all, delete-orphan'
    )


class MJ_Module(db.Model):
    __tablename__ = 'MultipleJoinModule'
    
    param_i = db.Column(db.Integer, primary_key=True, autoincrement=False, nullable=False)
    
    netApps_id = db.Column(db.Integer, db.ForeignKey('netApps.id'),
                              primary_key=True, autoincrement=False, nullable=False)
    df_object_id = db.Column(db.Integer, db.ForeignKey('df_object.id'), nullable=False)
    function_id = db.Column(db.Integer, db.ForeignKey('function.id'), nullable=True)
    
    df_object = db.relationship('DF_Object', back_populates='mj_modules')
    function = db.relationship('Function', back_populates='mj_modules')
    
    def export(self) -> dict:
        data = ('param_i', 'df_object_id', 'function.fn_name')
        return self.to_dict(data)
