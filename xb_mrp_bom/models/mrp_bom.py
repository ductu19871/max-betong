from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # Override version field from mrp_bom_version module
    version = fields.Integer(default=0)


    mix_bom_id = fields.Many2one(
        'mrp.bom',
        string='Mix BOM',
        compute='_compute_mix_bom_id',
        store=True,
        readonly=False,
        copy=False
    )
    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Work Center',
        compute='_compute_workcenter_id',
        store=True,
        readonly=False,
        check_company=True,
        tracking=True
    )

    _sql_constraints = [
        ('check_unique_version', 'UNIQUE(version, product_tmpl_id, workcenter_id)', _('Version must be unique for a BoM product.')),
    ]

    @api.constrains('previous_bom_id', 'type')
    def _check_mix_bom(self):
        for bom in self.filtered(lambda b: b.type == 'mix'):
            if bom.previous_bom_id:
                raise UserError(_('You cannot set a previous BoM for a mix BoM.'))

    @api.depends('previous_bom_id')
    def _compute_mix_bom_id(self):
        for bom in self.filtered(lambda b: b.type != 'mix'):
                bom.mix_bom_id = bom.with_context(active_test=False).old_versions.filtered(lambda p: p.type == 'mix')[:1]

    @api.depends('type')
    def _compute_workcenter_id(self):
        for bom in self:
            if bom.type == 'mix':
                bom.workcenter_id = False

    def _get_new_bom_vals(self):
        vals = super()._get_new_bom_vals()
        if self.type == 'mix':
            vals['type'] = 'normal'
        return vals

    def _get_last_version_bom(self):
        self.ensure_one()
        boms = self.with_context(active_test=False).search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('workcenter_id', '=', self.workcenter_id.id),
        ])
        return boms.sorted(lambda p: p.version, reverse=True)[:1]

    def button_reactivate(self):
        self.ensure_one()
        if self.active:
            raise UserError(_('You cannot reactivate a active BoM.'))
        boms = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('workcenter_id', '=', self.workcenter_id.id),
        ])
        boms.button_historical()
        self.write({
            'active': True,
            'state': 'active'
        })
        return True

    def button_new_version(self):
        self.ensure_one()
        if (bom_current := self._get_last_version_bom()) and bom_current != self:
            error_msg = _(
                'The new version can only be created from the current version.\n'
                'Please access %(bom_current_version)s and then create the new version.',
                bom_current_version=f'Version {bom_current.version}'
            )
            action_error = {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.bom',
                'context': {'create': False},
                'res_id': bom_current.id,
                'view_mode': 'form',
                'views': [[False, 'form']]
            }
            raise RedirectWarning(error_msg, action_error, _('Access the current version'))
        
        if self.type == 'mix' and not self._context.get('from_wizard_create_new_version'):
            return {
                'name': _('New Version'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mrp.bom.create_new_version.wizard',
                'target': 'new',
                'context': {
                    'default_bom_id': self.id,
                },
            }
        else:
            return super(MrpBom, self.with_context(from_create_new_version=True)).button_new_version()
