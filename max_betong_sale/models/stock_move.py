from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class StockMove(models.Model):
    _inherit = 'stock.move'

    ticket_on_hold_id = fields.Many2one('mrp.production', string='Remix Ticket', check_company=True)

    @api.ondelete(at_uninstall=False)
    def _prevent_ticket_on_hold_line_deletion(self):
        for line in self:
            if line.ticket_on_hold_id:
                raise ValidationError(_(
                    "You cannot delete a component line %s of ticket on hold as it would impact the ticket on hold production" % line.product_id.display_name
                ))

    @api.constrains('product_id', 'product_uom_qty')
    def _check_ticket_on_hold_line(self):
        for line in self.filtered('ticket_on_hold_id'):
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if (
                line.product_id != line.ticket_on_hold_id.product_id
                or
                float_compare(line.product_uom_qty, line.ticket_on_hold_id.product_qty, precision_digits=precision) != 0
            ):
                raise ValidationError(_(
                    "You cannot change the product or quantity of a component line %s of ticket on hold as it would impact the ticket on hold production" % line.product_id.display_name
                ))

    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty_update_accumulated_qty(self):
        for move in self:
            picking = move.picking_id
            if not picking or picking.state == 'done':
                continue

            picking.accumulated_qty = picking._get_live_accumulated_qty()
