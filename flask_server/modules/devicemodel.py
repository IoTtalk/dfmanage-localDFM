"""
DeviceModel Module.

contains:

    op_create_device_model
    op_update_device_model
    op_delete_device_model
    op_get_device_model_list
    op_get_device_model_info
    op_search_device_model
"""

import sys
sys.path.append("..")
from modules.deviceparameter import DeviceParameter
from modules.dmdf import DMDFTag
from modules.interface import Interface
from modules.utils import CCMError, record_parser
from db import models
from db import db
from sqlalchemy import or_

class DeviceModel(Interface):
    """DeviceModel class."""

    def op_create_device_model(self, ctx, dm_name, df_list, dm_type='other', plural=None, device_only=None):
        """
        Create a new Device Model.

        Server will check the dm_name is not duplicate, and return a new dm_id on success.

        :param dm_name: <DeviceModel.dm_name>
        :param df_list: A list of Device Feature info, which contains df_id, tags, df_parameter, etc.
        :param dm_type: <DeviceModel.dm_type>. Optional, Legacy.
        :param plural: The flag for this model's feature selection. 
                       Use the checkbox (False) on the GUI or select (True), the default is False. Optional.
        :param device_only: The flag for click this model on the GUI.
                            Use the feature selection (False) or device selection (True), the default is False. Optional.
        :type dm_name: str
        :type df_list: List[<DeviceFeature>]
        :type dm_type: str
        :type plural: Boolean
        :type device_only: Boolean

        :return:
            {
                'dm_id': <DeviceModel.id>
            }
        """

        # Check if dm exist
        if self.op_search_device_model(ctx, dm_name):
            raise CCMError('Device Model "{}" already exists'.format(dm_name))

        # Check df_list is not empty
        if not df_list:
            raise CCMError('Feature list cannot be empty')

        # Create new DeviceModel
        new_dm = models.DeviceModel(
            dm_name=dm_name,
            plural=plural or False,
            device_only=device_only or False,
        )
        db.session.add(new_dm)
        db.session.commit()

        # TODO: Check case of df_id not found

        # Create new DM_DF and DeviceParameter
        for df in df_list:
            # Create new DM_DF
            new_dmdf = models.DM_DF(
                dm_id=new_dm.id,
                df_id=df['df_id'],
            )
            db.session.add(new_dmdf)
            db.session.commit()

            # Save DeviceParameter
            DeviceParameter.op_create_device_parameter(
                ctx,
                dmdf_id=new_dmdf.id,
                df_parameter=df['df_parameter'],
            )

            # Save DM_DF_Tag
            DMDFTag.op_save_dm_df_tag(
                ctx,
                mf_id=new_dmdf.id,
                tags=df.get('tags', []),
            )

        return {'dm_id': new_dm.id}

    def op_update_device_model(self, ctx, dm_id, dm_name, df_list, dm_type='other', plural=None, device_only=None):
        """
        Update Device Model.

        Server will check the dm_name and dm_id is equal to DB,
        and check Device Model is not in use,
        then update and return the dm_id on success.

        :param dm_id: <DeviceModel.id>
        :param dm_name: <DeviceModel.dm_name>
        :param df_list: a list of Device Feature info, conains df_id, tags, df_parameter, etc
        :param dm_type: <DeviceModel.dm_type>, optional, legacy
        :param plural: The flag for this model's feature selection
                       Use the checkbox (False) on the GUI or select (True). Optional.
        :param device_only: The flag for click this model on the GUI.
                            Use the feature selection or device selection. Optional.
        :type dm_id: int
        :type dm_name: str
        :type plural: Boolean
        :type device_only: Boolean
        :type df_list: List[<DeviceFeature>]
        :type dm_type: str

        :return:
            {
                'dm_id': <DeviceModel.id>
            }
        """

        # check df_list not empty
        if not df_list:
            raise CCMError('Feature list cannot be empty')

        # check dm exist
        dm_record = db.session.query(models.DeviceModel).filter(models.DeviceModel.dm_name == dm_name).first()
        if not dm_record:
            raise CCMError('Device Model not found')

        dm_id = dm_record.id

        # check dm in use
        do_records = db.session.query(models.DeviceObject).filter(models.DeviceObject.dm_id == dm_id).all()
        if do_records:
            raise CCMError('Device Model is in use.')

        # update plural
        if plural:
            dm_record.plural = plural
            db.session.commit()

        # update device_only
        if device_only:
            dm_record.device_only = device_only
            db.session.commit()

        # TODO: fix user setting mf
        old_mf_records = (db.session.query(models.DM_DF).filter(models.DM_DF.dm_id == dm_id))
        old_mf_records = {mf.df_id: mf for mf in old_mf_records}
        
        # save DM_DF and DF_Parameter and DM_DF_Tag
        for df in df_list:
            if int(df['df_id']) in old_mf_records:
                old_mf_records.pop(int(df['df_id']))
            # update DF_Parameter
            DeviceParameter.op_update_device_parameter(
                ctx,
                dm_id=dm_id,
                df_id=df['df_id'],
                df_parameter=df.get('df_parameter', [])
            )

            # update new DM_DF_Tag
            DMDFTag.op_save_dm_df_tag(
                ctx,
                dm_id=dm_id,
                df_id=df['df_id'],
                tags=df.get('tags', [])
            )

        # delete not use DeviceParameter, DM_DF_Tag, DM_DF
        for mf in old_mf_records.values():
            (db.session.query(models.DeviceParameter)
                       .filter(models.DeviceParameter.dmdf_id == mf.id)
                       .delete())
            (db.session.query(models.DM_DF_Tag)
                       .filter(models.DM_DF_Tag.dmdf_id == mf.id)
                       .delete())
            (db.session.query(models.DM_DF)
                       .filter(models.DM_DF.id == mf.id)
                       .delete())
            db.session.commit()

        return {'dm_id': dm_id}

    def op_delete_device_model(self, ctx, dm_id):
        """
        Delete a Device Model by given dm_id.

        Server will check the Device Model is used or not, and return dm_id on success.

        :param dm_id: <DeviceModel.id>
        :type dm_id: int

        :return:
            {
                'dm_id': <DeviceModel.id>
            }
        """

        # check exist
        dm_record = db.session.query(models.DeviceModel).filter(models.DeviceModel.id == dm_id).first()
        if not dm_record:
            raise CCMError('Device Model not found')

        # check in use
        do_records = db.session.query(models.DeviceObject.dm_id).filter(models.DeviceObject.dm_id == dm_id).all()

        d_records = db.session.query(models.Device.dm_id).filter(models.Device.dm_id == dm_id).all()
        if do_records or d_records:
            raise CCMError('Device Model is in use.')

        # delete DM_DF, DF_Parameter, DM_DF_Tag
        mf_records = db.session.query(models.DM_DF).filter(models.DM_DF.dm_id == dm_id).all()
        for mf_record in mf_records:
            DeviceParameter.op_delete_device_parameter(ctx, mf_id=mf_record.id)
            DMDFTag.op_delete_dm_df_tag(ctx, mf_id=mf_record.id)
            db.session.delete(mf_record)
            db.session.commit()

        db.session.delete(dm_record)
        db.session.commit()

        return {'dm_id': dm_id}

    def op_get_device_model_list(self, ctx):
        """
        Get list of all device models without device features info.

        :return:
            {
                'dm_list': [<DeviceModel>, ...]
            }
        """
        user_id = ctx.u_id

        dm_records = (db.session.query(models.DeviceModel)
                                .select_from(models.DeviceModel)
                                .join(models.DM_DF)
                                .join(models.DeviceParameter)
                                .filter(or_(models.DeviceParameter.user_id == user_id,
                                            models.DeviceParameter.user_id == 1))
                                .group_by(models.DeviceModel.id)
                                .order_by(models.DeviceModel.dm_name)
                                .all())

        dm_list = []
        for dm_record in dm_records:
            dm_list.append(record_parser(dm_record))

        return {'dm_list': dm_list}

    def op_get_device_model_info(self, ctx, dm_id):
        """
        Get single device model info, like name and device features.

        :param dm_id: <DeviceModel.dm_id>
        :type dm_id: int

        :return:
            {
                <DeviceModel>,
                'df_list': [ <DeviceFeature>, ...] # with tag_id
            }
        """
        user_id = ctx.u_id

        # query DeviceModel
        dm_record = db.session.query(models.DeviceModel).filter(models.DeviceModel.id == dm_id).first()
        if dm_record is None:
            raise CCMError('Device Model id "{}" not found'.format(dm_id))

        dm = record_parser(dm_record)
        dm['df_list'] = []

        # query DeviceFeature
        df_records = (db.session.query(models.DeviceFeature)
                                .select_from(models.DM_DF)
                                .join(models.DeviceFeature,
                                      models.DeviceFeature.id == models.DM_DF.df_id)
                                .join(models.DeviceParameter,
                                      models.DeviceParameter.dmdf_id == models.DM_DF.id)
                                .filter(models.DM_DF.dm_id == dm_id,
                                        or_(models.DeviceParameter.user_id == user_id,
                                            models.DeviceParameter.user_id == 1))
                                .group_by(models.DeviceFeature.id)
                                .order_by(models.DeviceFeature.df_name)
                                .all())

        for df_record in df_records:
            df = record_parser(df_record)
            df['df_parameter'] = DeviceParameter.op_get_device_parameter(
                ctx,
                df_id=df['id'],
                dm_id=dm_id
            )['df_parameter']
            df.update(DMDFTag.op_get_dm_df_tag(
                    ctx,
                    df_id=df['id'],
                    dm_id=dm_id
                )
            )
            dm['df_list'].append(df)

        return dm

    def op_search_device_model(self, ctx, dm_name):
        """
        Check DeviceModel name is in use.

        :param dm_name: <DeviceModel.dm_name>

        :return:
            <DeviceModel.id> / None
        """
        dm_record = db.session.query(models.DeviceModel).filter(models.DeviceModel.dm_name == dm_name).first()
        return (dm_record.id if dm_record else None)
