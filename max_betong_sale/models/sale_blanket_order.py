from odoo import models, fields, api

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