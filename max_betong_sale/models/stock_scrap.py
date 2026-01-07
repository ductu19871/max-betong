# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'
    
    def action_validate(self):
        for this in self:
            if this.production_id:
                this.production_id.write({'state':'dump'})
        return super().action_validate()