# -*- coding: utf-8 -*-
# Copyright 2022 IZI PT Solusi Usaha Mudah
from odoo import models
from odoo.exceptions import ValidationError


class IZIAnalysisDBOdoo(models.Model):
    _inherit = 'izi.analysis'

    def get_analysis_datas_db_odoo(self, **kwargs):
        self.ensure_one()
        cursor = self.source_id.get_cursor_db_odoo()

        try:
            cursor.execute(kwargs.get('query'))
        except Exception as e:
            raise ValidationError(e)
        res_data = self.source_id.dictfetchall_db_odoo(cursor)
        self.source_id.close_cursor_db_odoo(cursor)
        return {
            'res_data': res_data,
        }

    def get_field_metric_format_db_odoo(self, **kwargs):
        self.ensure_one()
        query = '%s' % (kwargs.get('field_name'))
        if not kwargs.get('field_format'):
            return query
        if kwargs.get('field_type') in ('date', 'datetime'):
            field_query = {
                'year': "to_char(date_trunc('year', %s), 'YYYY')" % kwargs.get('field_name'),
                'month': "to_char(date_trunc('month', %s), 'Mon YYYY')" % kwargs.get('field_name'),
                'week': "concat('Week ', to_char(date_trunc('week', %s), 'WW'), ' ', " % kwargs.get('field_name')
                + "to_char(date_trunc('year', %s), 'YYYY'))" % kwargs.get('field_name'),
                'day': "to_char(date_trunc('day', %s), 'DD Mon YYYY')" % kwargs.get('field_name'),
            }
            if kwargs.get('field_format') in field_query:
                query = field_query.get(kwargs.get('field_format'))
        return query

    def get_field_dimension_format_db_odoo(self, **kwargs):
        self.ensure_one()
        query = '%s' % kwargs.get('field_name')
        if not kwargs.get('field_format'):
            return query
        if kwargs.get('field_type') in ('date', 'datetime'):
            field_query = {
                'year': "date_trunc('year', %s)" % kwargs.get('field_name'),
                'month': "date_trunc('month', %s)" % kwargs.get('field_name'),
                'week': "date_trunc('week', {field_name}), date_trunc('year', {field_name})".format(
                    field_name=kwargs.get('field_name')),
                'day': "date_trunc('day', %s)" % kwargs.get('field_name'),
            }
            if kwargs.get('field_format') in field_query:
                query = field_query.get(kwargs.get('field_format'))
        return query

    def get_field_sort_format_db_odoo(self, **kwargs):
        self.ensure_one()
        query = '%s %s' % (kwargs.get('field_name'), kwargs.get('sort'))
        if not kwargs.get('field_format'):
            return query
        if kwargs.get('field_type') in ('date', 'datetime'):
            field_query = {
                'year': "date_trunc('year', %s) %s" % (kwargs.get('field_name'), kwargs.get('sort')),
                'month': "date_trunc('month', %s) %s" % (kwargs.get('field_name'), kwargs.get('sort')),
                'week': "date_trunc('week', {field_name}) {sort}, date_trunc('year', {field_name}) {sort}".format(
                    field_name=kwargs.get('field_name'), sort=kwargs.get('sort')),
                'day': "date_trunc('day', %s) %s" % (kwargs.get('field_name'), kwargs.get('sort')),
            }
            if kwargs.get('field_format') in field_query:
                query = field_query.get(kwargs.get('field_format'))
        return query

    def get_filter_query_db_odoo(self, **kwargs):
        self.ensure_one()
        filter_result = False
        filter_field = kwargs.get('filter_value')[0]
        filter_type = kwargs.get('filter_value')[1]
        filter_list = kwargs.get('filter_value')[2]

        if filter_type == 'string_search':
            string_search_query = []
            for value in filter_list:
                string_search_query.append("%s ilike '%s'" % (filter_field, '%' + value + '%'))
            filter_result = {
                'query': string_search_query,
                'join_operator': 'or'
            }

        elif filter_type == 'date_range':
            date_range_query = []

            start_date = filter_list[0]

            end_date = False
            if len(filter_list) == 2:
                end_date = filter_list[1]

            if start_date is not False and start_date is not None:
                date_range_query.append("%s >= '%s'" % (filter_field, start_date))

            if end_date is not False and end_date is not None:
                date_range_query.append("%s <= '%s'" % (filter_field, end_date))

            filter_result = {
                'query': date_range_query,
                'join_operator': 'and'
            }

        elif filter_type == 'date_format':
            date_format_query = []

            date_format = filter_list[0]

            date_range = self.get_date_range_by_date_format(date_format)

            start_date = date_range.get('start_date')
            end_date = date_range.get('end_date')

            if start_date is not False and start_date is not None:
                date_format_query.append("%s >= '%s'" % (filter_field, start_date))

            if end_date is not False and end_date is not None:
                date_format_query.append("%s <= '%s'" % (filter_field, end_date))

            filter_result = {
                'query': date_format_query,
                'join_operator': 'and'
            }

        return filter_result
