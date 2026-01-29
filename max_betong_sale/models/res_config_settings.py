# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    concrete_load_volume = fields.Float(
        related="company_id.concrete_load_volume", readonly=False,
        string='Concrete Load Volume',
    )
    
    @api.constrains('concrete_load_volume')
    def _check_concrete_load_volume(self):
        for rec in self:
            if rec.concrete_load_volume <= 0:
                raise ValidationError(
                    _("Concrete Load Volume must be greater than 0.")
                )