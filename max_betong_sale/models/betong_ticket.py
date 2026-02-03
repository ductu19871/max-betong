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
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        related='sale_order_id.company_id',
        store=True
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
        for vals in vals_list:
            if 'company_id' not in vals and 'sale_order_id' in vals:
                sale_order = self.env['sale.order'].browse(vals['sale_order_id'])
                if sale_order.exists():
                    vals['company_id'] = sale_order.company_id.id
            if 'company_id' not in vals:
                vals['company_id'] = self.env.company.id
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

