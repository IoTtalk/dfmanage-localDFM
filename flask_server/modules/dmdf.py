"""
DMDF Tag Module.

contains:

    op_save_dm_df_tag
    op_delete_dm_df_tag
    op_get_dm_df_tag

"""

import sys
sys.path.append("..")
from modules.interface import Interface
from modules.utils import CCMError, record_parser
from db import models
from db import db

class DMDFTag(Interface):
    def op_save_dm_df_tag(self, ctx, tags, df_id=None, dm_id=None, mf_id=None):
        """
        Create/Update Device Feature Tags for DeviceModel.

        You need supply (`df_id`, `dm_id` ) or (`mf_id`) to update DM_DF.

        :param tags: The device feature tags
        :param df_id: <DeviceFeature.id>, optional
        :param dm_id: <DeviceModel.id>, optional
        :param mf_id: <DM_DF.id>, optional
        :type tags: List[<Tag.id>]
        :type df_id: int
        :type dm_id: int
        :type mf_id: int

        :return:
            {
                'mf_id': '<DM_DF.id>'
            }
        """
        db_session = ctx.db_session

        if df_id and dm_id:
            # if given df_id and dm_id, query mf_id first
            mf_record = (db_session.query(model.DM_DF)
                                   .filter(model.DM_DF.df_id == df_id,
                                           model.DM_DF.dm_id == dm_id)
                                   .first())
            if mf_record:
                mf_id = mf_record.mf_id
            else:
                raise CCMError('can\'t find DM_DF for given dm_id and df_id.')
        elif not mf_id:
            raise CCMError('one of "df_id" or "mf_id" should be supplied.')

        # delete old first
        self.op_delete_dm_df_tag(ctx, mf_id=mf_id)

        # update DM_DF tag
        for tag in tags:
            new_mf_tag = model.DM_DF_Tag(
                mf_id=mf_id,
                tag_id=tag.get('tag_id'))
            db_session.add(new_mf_tag)
            db_session.commit()

        return {'mf_id': mf_id}

    def op_delete_dm_df_tag(self, ctx, df_id=None, dm_id=None, mf_id=None):
        """
        Delete Tag for DM_DF.

        You need supply (`df_id`, `dm_id` ) or (`mf_id`) to query DM_DF.

        :param df_id: <DeviceFeature.df_id>, optional
        :param dm_id: <DeviceModel.dm_id>, optional
        :param mf_id: <DM_DF.mf_id>, optional
        :type df_id: int
        :type dm_id: int
        :type mf_id: int

        :return:
            {
                'mf_id': mf_id
            }
        """
        db_session = ctx.db_session

        if dm_id and df_id:
            # if given df_id and dm_id, query mf_id first
            mf_record = (db_session.query(model.DM_DF)
                                   .filter(model.DM_DF.df_id == df_id,
                                           model.DM_DF.dm_id == dm_id)
                                   .first())
            if mf_record:
                mf_id = mf_record.mf_id
            else:
                raise CCMError('can\'t find DM_DF for given dm_id and df_id.')
        elif not mf_id:
            raise CCMError('(df_id, dm_id) or mf_id should be supplied.')

        (db_session
            .query(model.DM_DF_Tag)
            .filter(model.DM_DF_Tag.mf_id == mf_id)
            .delete())

        return {'mf_id': mf_id}

    def op_get_dm_df_tag(self, ctx, df_id=None, dm_id=None, mf_id=None):
        """
        Get Tag for DM_DF.

        You need supply (`df_id`, `dm_id` ) or (`mf_id`) to query DM_DF.

        :param df_id: <DeviceFeature.df_id>, optional
        :param dm_id: <DeviceModel.dm_id>, optional
        :param mf_id: <DM_DF.mf_id>, optional
        :type df_id: int
        :type dm_id: int
        :type mf_id: int

        :return:
            {
                'tags': [<Tag>, ...]
            }
        """
        db_session = ctx.db_session

        if dm_id and df_id:
            # if given df_id and dm_id, query mf_id first
            mf_record = (db_session.query(model.DM_DF)
                                   .filter(model.DM_DF.df_id == df_id,
                                           model.DM_DF.dm_id == dm_id)
                                   .first())
            if mf_record:
                mf_id = mf_record.mf_id
            else:
                raise CCMError('can\'t find DM_DF for given dm_id and df_id.')
        elif not mf_id:
            raise CCMError('(df_id, dm_id) or mf_id should be supplied.')

        tag_records = (db_session.query(model.Tag)
                                 .select_from(model.DM_DF_Tag)
                                 .join(model.Tag)
                                 .filter(model.DM_DF_Tag.mf_id == mf_id)
                                 .all())
        return {'tags': [record_parser(tag) for tag in tag_records]}
