from odoo import api, fields, models, Command, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.osv.expression import AND


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    # Override version field from mrp_bom_version module
    version = fields.Integer(default=0)


    mix_bom_id = fields.Many2one(
        'mrp.bom',
        string='Mix BOM',
        readonly=False
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

    @api.constrains('version', 'product_tmpl_id', 'workcenter_id')
    def _check_version_bom(self):
        for rec in self:
            for bom in rec.sudo()._get_all_version_boms().filtered(lambda b: b != rec):
                if bom.version == rec.version:
                    raise UserError(_('The version %(version)s is already used for the BoM product %(product)s.', version=rec.version, product=rec.product_tmpl_id.display_name))

    @api.constrains('previous_bom_id', 'type')
    def _check_mix_bom(self):
        for bom in self.filtered(lambda b: b.type == 'mix'):
            if bom.previous_bom_id:
                raise UserError(_('The Mix BoM product %(product)s must not have a previous BoM.', product=bom.product_tmpl_id.display_name))
            mix_boms = bom.sudo()._get_all_version_boms().filtered(lambda b: b != bom and b.type == 'mix')
            if mix_boms:
                raise UserError(_('The Mix BoM product %(product)s is available.', product=bom.product_tmpl_id.display_name))

    @api.depends('type')
    def _compute_workcenter_id(self):
        for bom in self:
            if bom.type == 'mix':
                bom.workcenter_id = False

    def _get_new_bom_vals(self):
        vals = super()._get_new_bom_vals()
        if self.type == 'mix':
            vals['type'] = 'normal'
            vals['mix_bom_id'] = self.id
        return vals

    def _bom_find_domain(self, products, picking_type=None, company_id=False, bom_type=False):
        domain = super()._bom_find_domain(products, picking_type, company_id, bom_type)
        if workcenter_id := self._context.get('workcenter_id'):
            domain = AND([domain, [('workcenter_id', '=', workcenter_id)]])
        return domain

    def _get_all_version_boms(self, active_test=False):
        self.ensure_one()
        products = self.product_id or self.product_tmpl_id.product_variant_ids
        domain = self.with_context(workcenter_id=self.workcenter_id.id)._bom_find_domain(
            products,
            company_id=self.company_id.id
        )
        boms = self.search(domain)
        if not active_test:
            domain = [
                ('active', '=', False) if (isinstance(item, tuple) and item == ('active', '=', True)) else item
                for item in domain
            ]
            boms |= self.search(domain)
        return boms

    def _get_last_version_bom(self, active_test=False):
        self.ensure_one()
        return self._get_all_version_boms(active_test).sorted(lambda p: int(p.version), reverse=True)[:1]

    def button_reactivate(self):
        self.ensure_one()
        if self.active:
            raise UserError(_('You cannot reactivate a active BoM.'))
        boms = self._get_all_version_boms(active_test=True)
        boms.button_historical()
        self.write({
            'active': True,
            'state': 'active'
        })
        return True

    def button_new_version(self):
        self.ensure_one()
        if self.type != 'mix' and (bom_current := self._get_last_version_bom()) and bom_current != self:
            error_msg = _(
                'The new version can only be created from the current version.\n'
                'Please access %(bom_current_version)s and then create the new version.',
                bom_current_version=f'BoM product {bom_current.product_tmpl_id.display_name} version {bom_current.version}'
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

    def write(self, vals):
        result = super(MrpBom, self).write(vals)
        if vals.get('active') == True:
            for bom in self:
                productions = self.env['mrp.production'].sudo().search([
                    '|',
                    ('bom_id.product_id', '=', bom.product_id.id),
                    ('bom_id.product_tmpl_id', '=', bom.product_tmpl_id.id),
                    ('bom_id.workcenter_id', '=', bom.workcenter_id.id),
                    ('state_concrete', 'in', ['draft', 'assigned'])
                ])
                if productions and (last_version_bom := bom._get_last_version_bom(active_test=True)):
                    productions.write({
                        'bom_id': last_version_bom.id
                    })
        return result
