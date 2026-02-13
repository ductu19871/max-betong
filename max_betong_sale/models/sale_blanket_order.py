from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleBlanketOrder(models.Model):
    _inherit = 'sale.blanket.order'

    so_type = fields.Selection(
        [
            ('concrete', 'Concrete'),
            ('normal', 'Normal'),
        ],
        string='SO Type',
        default='normal',
    )

    def action_view_sale_orders(self):
        if self.so_type == 'concrete':
            sale_orders = self._get_sale_orders()
            action = self.env["ir.actions.act_window"]._for_xml_id("max_betong_sale.action_concrete_orders")
            if len(sale_orders) > 0:
                action["domain"] = [("id", "in", sale_orders.ids)]
                action["context"] = [("id", "in", sale_orders.ids)]
            else:
                action = {"type": "ir.actions.act_window_close"}
            return action
        else:
            return super().action_view_sale_orders()
        
    @api.constrains('product_uom_qty')
    def _check_product_uom_qty(self):
        for r in self:
            if r.product_uom_qty < 10:
                raise ValidationError(
                                    _("Original product quantity  must be greater than or equal to 10.")
                                )