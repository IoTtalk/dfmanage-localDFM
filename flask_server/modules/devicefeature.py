"""
DeviceFeature Module.

contains:

    op_create_device_feature
    op_update_device_feature
    op_delete_device_feature
    op_get_device_feature_list
    op_get_device_feature_info
    op_search_device_feature
"""

import sys
sys.path.append("..")
from modules.devicefeatureparameter import DeviceFeatureParameter
from modules.interface import Interface
from modules.utils import CCMError, record_parser
from db import models
from db import db

class DeviceFeature(Interface):
    """Device Feature class."""

    # The df_user should set different by identifing the user name of every localDFM server.
    def op_create_device_feature(self, ctx, df_name, df_type, df_parameter, content='', df_user='nycu'):
        """
        Create a new Device Feature, and return the id of new Device Feature.
        
        The name of new Device Feature will be checked whether the default user have created another DF with the same name.

        :type df_name: str
        :type df_type: str, in ['idf', 'odf']
        :type df_parameter: List[<DF_Parameter>]
        :type content: str
        :type df_user: str
        :param df_name: <DeviceFeature.df_name>
        :param df_type: <DeviceFeature.df_type>
        :param param_num: The numbers of device feature parameters (attributes)
        :param content: <DeviceFeature.content>, optional
        :param user: <DeviceFeature.user>

        :return:
            {
                'df_id': <DeviceFeature.id>
            }
        """

        # Check whether the df_user is exist in user table of database.
        user = models.User.query.filter_by(username=df_user).first()
        if not user:
            raise CCMError('User "{}" is not a valid user stored in database'.format(df_user))
        
        # Check DeviceFeature name is in use with the user.
        # Notice that the same df name with different users can exist at the same time.
        if self.op_search_device_feature(ctx, df_name, df_user):
            raise CCMError('Device Feature "{}" already exists'.format(df_name))

        if df_type not in ('idf', 'odf'):
            raise CCMError('Invalid feature type "{}"'.format(df_type))

        if len(df_parameter) == 0:
            raise CCMError('df_parameter is empty')

        # Create new DeviceFeature
        new_df = models.DeviceFeature(
            df_name=df_name,
            df_type=df_type,
            param_num=len(df_parameter),
            content=content,
            user=df_user,
        )
        db.session.add(new_df)
        db.session.commit()

        # Create new DF_Parameter
        DeviceFeatureParameter.op_create_device_feature_parameter(
            ctx,
            df_id=new_df.id,
            df_user=df_user,
            df_parameter=df_parameter,
        )

        return {'df_id': new_df.id}

    def op_update_device_feature(self, ctx, df_id, df_name, df_type, df_parameter, content='', df_user='nycu'):
        """
        Update the Device Feature info.

        If success update, server will return df_id.

        :type df_name: str
        :type df_type: str, in ['idf', 'odf']
        :type df_parameter: List[<DF_Parameter>]
        :type content: str
        :type df_user: str
        :param df_name: <DeviceFeature.df_name>
        :param df_type: <DeviceFeature.df_type>
        :param param_num: The numbers of device feature parameters (attributes)
        :param content: <DeviceFeature.content>, optional
        :param user: <DeviceFeature.user>

        :return:
            {
                'df_id': <DeviceFeature.id>
            }
        """

        # Check DeviceFeature exist
        df_record = (db.session.query(models.DeviceFeature).filter(models.DeviceFeature.id == df_id).first())
        if not df_record:
            raise CCMError('Device Feature not found')

        # Update fields
        df_record.df_type = df_type
        df_record.content = content
        df_record.user = df_user
        df_record.param_num = len(df_parameter)
        db.session.commit()
        
        # Update DF_Parameter
        DeviceFeatureParameter.op_update_device_feature_parameter(
            ctx,
            df_id=df_id,
            df_user=df_user,
            df_parameter=df_parameter,
        )

        return {'df_id': df_id}

    def op_delete_device_feature(self, ctx, df_id):
        """
        Delete a Device Feature by given df_id.

        Server will check the Device Feature is used or not.
        If delete successful, server will return df_id.

        :type df_id: int
        :param df_id: <DeviceFeature.id>

        :return:
            {
                'df_id': <DeviceFeature.df_id>
            }
        """

        # Check existence
        df = (db.session.query(models.DeviceFeature).filter(models.DeviceFeature.id == df_id).first())
        if df is None:
            raise CCMError('Device Feature id {} not found'.format(df_id))

        # Check in use
        mf_records = (db.session.query(models.DM_DF).filter(models.DM_DF.df_id == df_id).all())
        
        dfo_records = (db.session.query(models.DF_Object).filter(models.DF_Object.df_id == df_id).all())

        if mf_records or dfo_records:
            raise CCMError('Device Feature is in use.')

        # delete DeviceParameter
        db.session.query(models.DeviceParameter).filter(models.DeviceParameter.df_id == df_id).delete()

        # delete FunctionSDF
        db.session.query(models.FunctionSDF).filter(models.FunctionSDF.df_id == df_id).delete()

        # delete DeviceFeature
        db.session.query(models.DeviceFeature).filter(models.DeviceFeature.df_id == df_id).delete()
        db.session.commit()

        return {'df_id': df_id}

    def op_get_device_feature_list(self, ctx, df_user='nycu'):
        """
        Get all Device Features (by category).

        Server will return two lists,
        input and output Device Feature list.

        If `df_category` is given, category will be used as search condition.

        :param user: <DeviceFeature.user>
        :type df_user: str

        :return:
            {
                'idf': [<DeviceFeature>, ...],
                'odf': [<DeviceFeature>, ...]
            }
        """

        df_records = (db.session.query(models.DeviceFeature).filter(models.DeviceFeature.user == df_user).order_by(models.DeviceFeature.df_name).all())
        
        result = {
            'idf': [],
            'odf': []
        }
        
        for df_record in df_records:
            result[df_record.df_type].append(record_parser(df_record))

        return result

    def op_get_device_feature_info(self, ctx, df_id, df_user='nycu'):
        """
        Get the Device Feature's information detail.

        :param df_id: <DeviceFeature.id>
        :type df_id: int

        :return:
            {
                'df_id': <DeviceFeature.id>,
                'df_name': <DeviceFeature.df_name>,
                'dt_type': <DeviceFeature.df_type>,
                'param_num': <DeviceFeature.param_num>, # number of parameters
                'content': <DeviceFeature.content>,
                'df_parameter': [<DF_Parameter>, ...]
            }
        """

        # query DeviceFeature
        df_record = (db.session.query(models.DeviceFeature).filter(models.DeviceFeature.id == df_id).first())

        if not df_record:
            raise CCMError('Device Feature id {} not found'.format(df_id))

        df_info = record_parser(df_record)
        df_info['df_parameter'] = (self.op_get_device_feature_parameter(ctx, df_user, df_id).get('df_parameter', []))

        return df_info

    def op_search_device_feature(self, ctx, df_name, df_user):
        """
        Seach Device Feature by name.

        If in use, return df_id, else return None.

        :param df_name: <DeviceFeature.df_name>
        :param user: <DeviceFeature.user>
        :type df_name: str
        :type df_user: str

        :return:
            <DeviceFeature.id> / None
        """

        df_record = (db.session.query(models.DeviceFeature).filter(models.DeviceFeature.df_name == df_name, models.DeviceFeature.user == df_user).first())
        return (df_record.id if df_record else None)
