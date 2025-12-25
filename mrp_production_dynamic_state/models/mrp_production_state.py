# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MrpProductionState(models.Model):
    _name = 'mrp.production.state'
    _description = 'MRP Production State'
    _order = 'sequence, id'

    name = fields.Char(
        string='Name',
        required=True,
    )
    code = fields.Char(
        string='State Code',
        required=True,
        help='Unique code for the dynamic state'
    )
    original_state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('progress', 'In Progress'),
            ('to_close', 'To Close'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
        string='Original State',
        required=True,
        help='Original state from mrp.production to map to this dynamic state'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence for ordering states'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, this mapping will be hidden'
    )
    description = fields.Text(
        string='Description',
        help='Description of this dynamic state'
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'State code must be unique!'),
    ]

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if not rec.code or not rec.code.strip():
                raise ValidationError(_('State code cannot be empty.'))
            if not rec.code.replace('_', '').isalnum():
                raise ValidationError(_('State code can only contain letters, numbers, and underscores.'))

