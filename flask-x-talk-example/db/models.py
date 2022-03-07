import datetime

import pytz
from flask_login import UserMixin
from sqlalchemy import event

from ..const import UserGroup
from . import db


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


association_table = db.Table('association', db.Model.metadata,
                             db.Column('user_id',
                                       db.ForeignKey('user.id'), primary_key=True),
                             db.Column('permission_id',
                                       db.ForeignKey('permission.id'), primary_key=True))

association_content_table = db.Table('association_content', db.Model.metadata,
                                     db.Column('content_id',
                                               db.ForeignKey('content.id'),
                                               primary_key=True),
                                     db.Column('permission_id',
                                               db.ForeignKey('permission.id'),
                                               primary_key=True))


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
