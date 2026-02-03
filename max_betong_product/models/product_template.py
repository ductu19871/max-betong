# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_concrete_product = fields.Boolean(
        string='Is Concrete Product',
        default=False,
        help='Mark if this product is Concrete, managed separately according to Concrete product business.'
    )

    concrete_lifespan = fields.Integer(
        string='Concrete Lifespan',
        help='Time concrete can be used after mixing (in minutes). '
             'Used for quality control and delivery coordination. '
             'If transport or waiting time exceeds this value, concrete quality is not guaranteed.'
    )

    _sql_constraints = [
        ('unique_concrete_product_name', 
         'UNIQUE(name) WHERE is_concrete_product = TRUE',
         'Concrete product name must be unique. Another product with the same name already exists.')
    ]

    @api.constrains('name', 'is_concrete_product')
    def _check_unique_concrete_product_name(self):
        """Ensure concrete products have unique names."""
        for record in self:
            if record.is_concrete_product and record.name:
                domain = [
                    ('name', '=', record.name),
                    ('is_concrete_product', '=', True),
                    ('id', '!=', record.id)
                ]
                duplicate = self.search(domain, limit=1)
                if duplicate:
                    raise ValidationError(
                        _('Concrete product name must be unique. '
                          'Another product with the same name already exists.')
                    )
