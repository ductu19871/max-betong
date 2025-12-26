from odoo import models, fields, api, _

class HRTemplateParameter(models.Model):
    _name = 'report.template.parameter'
    _description = 'Report Template Parameter'
    _rec_name = 'name'
    _sql_constraints = [('unique_key', 'unique (key)', 'Key must be unique')]

    key = fields.Char(string='Model/Key')
    name = fields.Char(string='Name')
    model_filter = fields.Char(string='Model')
    template_ids = fields.One2many('report.template.config', 'parameter_id')
    description = fields.Html(string='Description')

    def action_unlink(self):
        self.template_ids.unlink()
        return {'type': 'ir.actions.act_window_close'}