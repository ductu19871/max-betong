# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_compare, float_round, format_date, groupby
from odoo.exceptions import ValidationError, UserError

class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'common.validation.mixin']

    @api.onchange('product_id')
    def _onchange_product_id(self):
        result = []
        if (self.order_id and 
            self.order_id.so_type == 'concrete' and 
            self.product_id and 
            not self.product_id.is_concrete_product):
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

    @api.constrains('product_template_id', 'product_uom_qty', 'product_uom')
    def _check_quantity_concrete_order(self):
        for line in self.filtered(lambda line: line.order_id.so_type == 'concrete' and line.blanket_order_line):
            if line.product_template_id != line.blanket_order_line.product_id.product_tmpl_id:
                raise UserError(_('The product is not the same as the blanket order line product.'))
            if line.product_uom != line.blanket_order_line.product_uom:
                raise UserError(_('The product UoM is not the same as the blanket order line product UoM.'))
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_current = sum(self.sudo().search([('blanket_order_line', '=', line.blanket_order_line.id), ('state', '!=', 'cancel')]).mapped('product_uom_qty'))
            if float_compare(qty_current, line.blanket_order_line.original_uom_qty, precision_digits=precision) > 0:
                raise UserError(_('The product quantity cannot be greater than the blanket order line original quantity.'))

    @api.constrains('product_uom_qty')
    def _check_product_uom_qty(self):
        not_display_lines = self.filtered(lambda rec: not rec.display_type)
        not_display_lines._validate_positive_with_decimal_limit('product_uom_qty', 1)


    def product_uom_change(self):
        concrete_so_lines = self.filtered(lambda line: line.order_id.so_type == 'concrete' and line.blanket_order_line)
        super(SaleOrderLine, concrete_so_lines.with_context(skip_blanket_find=True)).product_uom_change()
        super(SaleOrderLine, self - concrete_so_lines).product_uom_change()

    def onchange_product_id(self):
        concrete_so_lines = self.filtered(lambda line: line.order_id.so_type == 'concrete' and line.blanket_order_line)
        super(SaleOrderLine, self - concrete_so_lines).onchange_product_id()

    def _check_line_unlink(self):
        '''Ghi đè hàm gốc của odoo'''
        return self.filtered(
            lambda line:
                line.state == 'sale' and line.order_id.so_type !='bom'
                and (line.invoice_lines or not line.is_downpayment)
                and not line.display_type
        )
    
    @api.ondelete(at_uninstall=False)
    def _unlink_except_planned_pump_so(self):
        for line in self:
            if line.order_id.state == 'planned' and line.order_id.so_type == 'bom':
                raise UserError(_(
                    "You cannot delete a product line when the Pump Sales Order is in the Planned state."
                ))

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         order = self.env['sale.order'].browse(vals.get('order_id'))
    #         if order.state == 'planned' and  order.so_type == 'bom' :
    #             raise UserError(
    #                 "SO Bơm đang ở trạng thái Planned, không được thêm sản phẩm."
    #             )
    #     return super().create(vals_list)
    
    # def write(self, vals):
    #     allowed_fields = {'product_uom_qty', 'qty_to_invoice'}
    #     for line in self:
    #         if line.order_id.state == 'planned' and  line.order_id.so_type == 'bom' :
    #             if any(field not in allowed_fields for field in vals.keys()):
    #                 raise UserError(
    #                     "SO Bơm ở trạng thái Planned chỉ được thay đổi số lượng và qty_to_invoice."
    #                 )
    #     return super().write(vals)