# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ConcreteLoad(models.Model):
    _inherit = 'concrete.load'

    def _get_bom_assign_ticket(self):
        if self.load_station_id:
            return self.env['mrp.bom'].search([
                ('product_tmpl_id','=',self.product_id.product_tmpl_id.id),
                ('type','!=','mix'),
                ('workcenter_id','=',self.load_station_id.id)
            ], limit =1)
        return super()._get_bom_assign_ticket()
