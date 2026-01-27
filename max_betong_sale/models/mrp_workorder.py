from odoo import _, models,fields, api
from odoo.tools import float_round
from datetime import date,timedelta

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def write(self, vals):
        res = super().write(vals)
        if vals.get('state') == 'progress':
            for wo in self:
                production = wo.production_id
                if production.state == 'progress' and production.mo_type == 'concrete':
                    production.action_loading()
        return res

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible'
    )