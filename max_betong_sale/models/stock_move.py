from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
            if line.product_id != line.ticket_on_hold_id.product_id or line.product_uom_qty != line.ticket_on_hold_id.product_qty:
                raise ValidationError(_(
                    "You cannot change the product or quantity of a component line %s of ticket on hold as it would impact the ticket on hold production" % line.product_id.display_name
                ))
