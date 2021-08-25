import datetime

import pytz

from flask_login import UserMixin
from sqlalchemy.schema import DefaultClause

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


class User(TimestampMixin, UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    sub = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255))

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
