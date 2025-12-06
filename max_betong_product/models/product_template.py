# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_betong_product = fields.Boolean(
        string='Is Concrete Product',
        default=False,
        help='Mark if this product is Concrete, managed separately according to Concrete product business.'
    )

    betong_lifespan = fields.Float(
        string='Concrete Lifespan',
        digits=(16, 2),
        help='Time concrete can be used after mixing (in minutes). '
             'Used for quality control and delivery coordination. '
             'If transport or waiting time exceeds this value, concrete quality is not guaranteed.'
    )

