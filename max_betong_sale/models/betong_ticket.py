# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BetongTicket(models.Model):
    """
    Ticket model for Concrete SO
    This model needs to be created or extended from existing ticket model
    """
    _name = 'concrete.ticket'
    _description = 'Concrete Ticket'

    name = fields.Char(string='Ticket Name', required=True)
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade'
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('loading', 'Loading'),
            ('completed', 'Completed'),
            ('dum', 'Dum'),
            ('remix_swapped', 'Remix&Swapped'),
        ],
        string='State',
        default='draft'
    )

    @api.model_create_multi
    def create(self, vals_list):
        tickets = super(BetongTicket, self).create(vals_list)
        for ticket in tickets:
            if ticket.state == 'loading' and ticket.sale_order_id:
                ticket.sale_order_id._check_ticket_loading_and_update_state()
        return tickets

    def write(self, vals):
        result = super(BetongTicket, self).write(vals)
        if 'state' in vals and vals['state'] == 'loading':
            for ticket in self:
                if ticket.sale_order_id:
                    ticket.sale_order_id._check_ticket_loading_and_update_state()
        return result

