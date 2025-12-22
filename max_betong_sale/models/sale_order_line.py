# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        result = []
        if (self.order_id and 
            self.order_id.so_type == 'betong' and 
            self.product_id and 
            not self.product_id.is_betong_product):
            return {
                'warning': {
                    'title': 'Warning',
                    'message': 'Only Concrete products can be selected when SO Type = Concrete.'
                }
            }
        return result

