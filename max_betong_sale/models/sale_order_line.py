# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import float_is_zero, float_compare, float_round, format_date, groupby

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

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        super()._compute_qty_to_invoice()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.order_id.so_type =='concrete':
                line._compute_qty_to_invoice()
                if line.state !='done':
                    line.invoice_status = 'no'
                elif line.is_downpayment and line.untaxed_amount_to_invoice == 0:
                    line.invoice_status = 'invoiced'
                elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    line.invoice_status = 'to invoice'
                elif line.state == 'done' and line.product_id.invoice_policy == 'order' and\
                        line.product_uom_qty >= 0.0 and\
                        float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                    line.invoice_status = 'upselling'
                elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                    line.invoice_status = 'invoiced'
                else:
                    line.invoice_status = 'no'
                    
    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'state')
    def _compute_qty_to_invoice(self):
        super()._compute_qty_to_invoice()
        for line in self:
            if line.order_id.so_type =='concrete':
                if line.state == 'done' and not line.display_type:
                    if line.product_id.invoice_policy == 'order':
                        line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
                else:
                    line.qty_to_invoice = 0
                
                
                
                
                