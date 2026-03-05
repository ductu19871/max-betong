# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    is_readonly_product = fields.Boolean(store=False)
    dump_reason = fields.Text(string="Reason")
    
    def action_validate(self):
        for this in self:
            if this.production_id and this.production_id.mo_type == 'concrete':
                this.production_id.write({'state_concrete':'dump'})
                this.production_id.vehicle_id.state_concrete = 'not_available'
                this.production_id.on_hold_reason = this.dump_reason
        return super().action_validate()