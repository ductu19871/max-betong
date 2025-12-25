# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    stage_id = fields.Many2one(
        'mrp.production.state',
        string='Stage',
        help='Stage for manufacturing order'
    )

    def _update_state_from_stage(self, vals):
        """Update state from stage_id's original_state if stage_id is provided"""
        if 'stage_id' in vals:
            stage_id = vals.get('stage_id')
            if stage_id:
                stage = self.env['mrp.production.state'].browse(stage_id)
                if stage and stage.original_state:
                    vals['state'] = stage.original_state
            # If stage_id is cleared (False), don't change state

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update original state when stage_id is set"""
        for vals in vals_list:
            self._update_state_from_stage(vals)
        return super(MrpProduction, self).create(vals_list)

    def write(self, vals):
        """Override write to update original state when stage_id changes"""
        self._update_state_from_stage(vals)
        result = super(MrpProduction, self).write(vals)
        return result

