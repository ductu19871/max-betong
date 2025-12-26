from odoo import fields, models, api, tools, _


class ReportTemplateUnion(models.Model):
    _name = 'report.template.union'
    _description = "Report Template Union"
    _auto = False
    _rec_name = 'name'

    name = fields.Char(string='Name', readonly=True, translate=True)
    report_id = fields.Many2one('ir.actions.report', string='Report', readonly=True)
    template_id = fields.Many2one('report.template.config', string="Template", readonly=True)
    res_model = fields.Char(string='Model Name', readonly=True)

    @property
    def _table_query(self):
        sql = '''
            SELECT *
            FROM (%s) as rtu
            %s
        ''' % (self._union_sql_query(), self._where_sql_query())
        return sql

    def _union_sql_query(self):
        return """
            SELECT
                id,
                name,
                NULL AS template_id,
                id AS report_id,
                model AS res_model
            FROM ir_act_report_xml

            UNION
            
            SELECT
                -rtc.id,
                jsonb_build_object('en_US', rtc.name) AS name,
                rtc.id AS template_id,
                NULL AS report_id,
                rtc.model_id AS res_model
            FROM report_template_config rtc
        """

    def _where_sql_query(self):
        return ''

    # ------------------------------------------------------------------------------------------
    #  Function
    # ------------------------------------------------------------------------------------------

    def call_union_action(self, res_model, res_id):
        if self.template_id:
            url = '/web/mailmerge_report?res_model=%(res_model)s&res_id=%(res_id)s&template_id=%(template_id)s&report_name=report' % {
                'res_model': res_model,
                'res_id': res_id,
                'template_id': self.template_id.id
            }
            return {
                'type': 'ir.actions.act_url',
                'url': url,
                'target': 'current',
            }
        elif self.report_id:
            active_id = self.env[res_model].browse(res_id)
            return self.report_id.report_action(active_id)
        else:
            return {}