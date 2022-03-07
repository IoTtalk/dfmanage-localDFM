from enum import Enum


class UserGroup(str, Enum):
    # the values will be inserted into db after 'group' table is created
    # if the table is created before you modified these values, you should
    # drop the table and recreate it again.
    # or you may consider to use the fixtures or something else to init
    Administrator = 'Administrator'
    User = 'User'
