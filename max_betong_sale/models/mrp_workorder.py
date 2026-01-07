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
                if production.state == 'confirmed':
                    production.action_loading()
        if vals.get('state') == 'done':
            for wo in self:
                production = wo.production_id
                all_done = all(
                    w.state == 'done'
                    for w in production.workorder_ids
                )
                if all_done:
                    production.action_loaded()
        return res