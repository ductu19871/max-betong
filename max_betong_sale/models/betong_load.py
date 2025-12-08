# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BetongLoad(models.Model):
    """
    Load model for Concrete SO
    This model stores Load information allocated from SO
    """
    _name = 'concrete.load'
    _description = 'Concrete Load'

    name = fields.Char(string='Load Name', required=True)
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
        index=True
    )
    volume = fields.Float(
        string='Volume (m³)',
        required=True,
        help='Volume of this Load'
    )


