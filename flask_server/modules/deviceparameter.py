"""
Device Feature Parameter Module.

contains:

    op_create_device_parameter
    op_update_device_parameter
    op_delete_device_parameter
    op_get_device_parameter
"""

import sys
sys.path.append("..")
from modules.interface import Interface
from modules.utils import CCMError, record_parser
from db import models
from db import db


class DeviceParameter(Interface):
    """DeviceFeatureParameter class."""

    def op_create_device_parameter(self, ctx, df_parameter, df_user, df_id=None, dm_id=None, mf_id=None):
        """
        Create Device Feature Parameters for DeviceFeature/DM_DF.

        Server will save for logging user.
        You need supply (`df_id`, `dm_id` ) or (`mf_id`) to create DM_DF,
        or (`df_id`) to create DeviceFeature.

        :param df_parameter: The device feature parameters (attributes)
        :param df_id: <DeviceFeature.id>, optional
        :param dm_id: <DeviceModel.id>, optional
        :param mf_id: <DM_DF.id>, optional
        *** df_id and mf_id should be provided at least one of them.
        :type df_parameter: List[<DF_Parameter>]
        :type df_id: int
        :type dm_id: int
        :type mf_id: int

        :return:
            {
                'df_id': '<DeviceFeature.id>',
                'mf_id': '<DM_DF.id>',
            }
        """

        # Check query condition
        if df_id and dm_id:
            # If given df_id and dm_id, it means the device parameter belongs to a DM_DF, query mf_id first
            mf_record = db.session.query(models.DM_DF).filter(models.DM_DF.df_id == df_id, models.DM_DF.dm_id == dm_id).first()
            if mf_record:
                mf_id = mf_record.id
                df_id = None
            else:
                raise CCMError('Given "df_id" and "dm_id" not found.')
        elif not df_id and not mf_id:
            raise CCMError('One of [ "df_id" or "mf_id" ] should be supplied.')

        # save device feature parameter
        for dfp in enumerate(df_parameter):
            new_dfp = models.DeviceParameter(
                param_type=dfp.get('param_type', 'int'),
                idf_type=dfp.get('idf_type', 'sample'),
                min=dfp.get('min', 0),
                max=dfp.get('max', 0),
                dmdf_id=mf_id,
                df_id=df_id,
                unit_id=dfp.get('unit_id', 1),  # 1 for None
                fn_id=dfp.get('fn_id', None),
                user=df_user,
                normalization=dfp.get('normalization', 0),
            )
            db.session.add(new_dfp)
            db.session.commit()

        db.session.commit()

        return {'mf_id': mf_id} if mf_id else {'df_id': df_id}

    def op_update_device_parameter(self, ctx, df_parameter, df_user, df_id=None, dm_id=None, mf_id=None):
        """
        Update Device Feature Parameters for DeviceFeature/DM_DF.

        Server will save for logging user.
        You need supply (`df_id`, `dm_id` ) or (`mf_id`) to update DM_DF,
        or (`df_id`) to update DeviceFeature.

        :param df_parameter: The device feature parameters (attributes)
        :param df_id: <DeviceFeature.id>, optional
        :param dm_id: <DeviceModel.id>, optional
        :param mf_id: <DM_DF.id>, optional
        *** df_id and mf_id should be provided at least one of them.
        :type df_parameter: List[<DF_Parameter>]
        :type df_id: int
        :type dm_id: int
        :type mf_id: int

        :return:
            {
                'df_id': '<DeviceFeature.id>',
                'mf_id': '<DM_DF.id>',
            }
        """

        # Check query condition
        if mf_id:
            condition = (models.DeviceParameter.dmdf_id == mf_id)
        elif df_id and dm_id:
            # If given df_id and dm_id, query mf_id first
            mf_record = db.session.query(models.DM_DF).filter(models.DM_DF.df_id == df_id, models.DM_DF.dm_id == dm_id).first()
            if mf_record:
                mf_id = mf_record.id
                df_id = None
                condition = (models.DeviceParameter.dmdf_id == mf_id)
            else:
                # There's no dm_df with given df_id and dm_id in database, create new DM_DF
                new_mf = models.DM_DF(
                    dm_id=dm_id,
                    df_id=df_id
                )
                db.session.add(new_mf)
                db.session.commit()
                mf_id = new_mf.id
                df_id = None
                condition = (models.DeviceParameter.dmdf_id == mf_id)
        elif df_id:
            condition = (models.DeviceParameter.df_id == df_id)
        else:
            raise CCMError('One of [ "df_id" or "mf_id" ] should be supplied.')

        # update device feature parameter
        for dfp in enumerate(df_parameter):
            # try update first
            user = db.session.query(models.User).filter(models.User.username == df_user).first()
            update_dfp = db.session.query(models.DeviceParameter).filter(condition, models.DeviceParameter.user_id == user.id).update(dfp)

            db.session.commit()

            # if return value is 0 means update 0 rows, so create new one
            if update_dfp == 0:
                new_dfp = models.DF_Parameter(
                    param_type=dfp.get('param_type', 'int'),
                    idf_type=dfp.get('idf_type', 'sample'),
                    min=dfp.get('min', 0),
                    max=dfp.get('max', 0),
                    dmdf_id=mf_id,
                    df_id=df_id,
                    unit_id=dfp.get('unit_id', 1),  # 1 for None
                    fn_id=dfp.get('fn_id', None),
                    user_id=user.id,
                    normalization=dfp.get('normalization', 0),
                )
                db.session.add(new_dfp)
                db.session.commit()

        db.session.commit()

        return {'mf_id': mf_id} if mf_id else {'df_id': df_id}

    def op_delete_device_parameter(self, ctx, df_id=None, dm_id=None, mf_id=None):
        """
        Delete Device Feature Parameters for DeviceFeature/DM_DF.

        You need supply (`df_id`, `dm_id` ) or (`mf_id`) to delete DM_DF,
        or (`df_id`) to delete DeviceFeature.

        :param df_id: <DeviceFeature.id>, optional
        :param dm_id: <DeviceModel.id>, optional
        :param mf_id: <DM_DF.id>, optional
        *** df_id and mf_id should be provided at least one of them.
        :type df_id: int
        :type dm_id: int
        :type mf_id: int

        :return:
            {
                'mf_id': mf_id,
                'df_id': df_id
            }
        """

        if mf_id:
            condition = (models.DeviceParameter.dmdf_id == mf_id)
        elif df_id and dm_id:
            mf_record = db.session.query(models.DM_DF).filter(models.DM_DF.df_id == df_id, models.DM_DF.dm_id == dm_id).first()
            if mf_record:
                mf_id = mf_record.id
                df_id = None
                condition = (models.DeviceParameter.dmdf_id == mf_id)
            else:
                raise CCMError('Can not find DM_DF for given dm_id and df_id.')
        elif df_id:
            condition = (models.DeviceParameter.df_id == df_id)
        else:
            raise CCMError('One of [ "df_id" or "mf_id" ] should be supplied.')

        db.session.query(models.DeviceParameter).filter(condition).delete()
        db.session.commit()

        return {'mf_id': mf_id} if mf_id else {'df_id': df_id}

    def op_get_device_parameter(self, ctx, df_user, df_id=None, dm_id=None, mf_id=None):
        """
        Get Device Feature Parameters for DeviceFeature/DM_DF.

        It will query logging user setting first then general setting.
        You need supply (`df_id`, `dm_id` ) or (`mf_id`) to query DM_DF,
        or (`df_id`) to query DeviceFeature.

        :param df_id: <DeviceFeature.id>, optional
        :param dm_id: <DeviceModel.id>, optional
        :param mf_id: <DM_DF.id>, optional
        :type df_id: int
        :type dm_id: int
        :type mf_id: int

        :return:
            {
                'df_parameter': [<DF_Parameter>, ...]
            }
        """

        if mf_id:
            condition = (models.DeviceParameter.dmdf_id == mf_id)
        elif df_id and dm_id:
            mf_record = db.session.query(models.DM_DF).filter(models.DM_DF.df_id == df_id, models.DM_DF.dm_id == dm_id).first()
            if mf_record:
                mf_id = mf_record.id
                df_id = None
                condition = (models.DeviceParameter.dmdf_id == mf_id)
            else:
                raise CCMError('can not find DM_DF for given dm_id and df_id.')
        elif df_id:
            condition = (models.DeviceParameter.df_id == df_id)
        else:
            raise CCMError('one of "df_id" or "mf_id" should be supplied.')

        # query user DF_Parameter
        user = db.session.query(models.User).filter(models.User.username == df_user).first()
        dfp_records = db.session.query(models.DeviceParameter).filter(models.DeviceParameter.user_id == user.id, condition).all()

        if not dfp_records:
            # query general DF_Parameter
            dfp_records = db.session.query(models.DeviceParameter).filter(condition, models.DeviceParameter.user_id == 1).all()

        df_parameters = []
        for dfp_record in dfp_records:
            df_parameters.append(record_parser(dfp_record))

        return {'df_parameter': df_parameters}
