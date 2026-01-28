from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class MrpBomConcreteProduct(models.Model):
    _inherit = "mrp.bom"

    is_concrete_product = fields.Boolean(
        related='product_tmpl_id.is_concrete_product',
        store=True
    )

    @api.constrains('type', 'product_tmpl_id', 'is_concrete_product')
    def _check_concrete_product(self):
        for bom in self.filtered("is_concrete_product"):
            if bom.type != 'mix':
                mix_boms = self.env['mrp.bom'].sudo().with_context(active_test=False).search([
                    ('product_tmpl_id', '=', bom.product_tmpl_id.id),
                    ('type', '=', 'mix'),
                    ('id', '!=', bom.id)
                ])
                if not mix_boms:
                    raise UserError(_("The BoM concrete product %(product)s must have a Mix BoM.", product=bom.product_tmpl_id.display_name))

    @api.depends('version', 'workcenter_id')
    def _compute_display_name(self):
        boms_concrete = self.filtered(lambda bom: bom.is_concrete_product and bom.type != 'mix')
        super(MrpBomConcreteProduct, self - boms_concrete)._compute_display_name()
        for bom in boms_concrete:
            bom.display_name = f"{' - '.join(filter(None, [bom.workcenter_id.code, 'Version %s' % bom.version if bom.version else '']))}: {bom.product_tmpl_id.display_name or ''}"

    @api.model_create_multi
    def create(self, vals_list):
        if not self._context.get('from_create_new_version'):
            for vals in vals_list:
                if (bom_type := vals.get('type')) and bom_type != 'mix' and (product_tmpl_id := vals.get('product_tmpl_id')):
                    product_tmpl = self.env['product.template'].browse(product_tmpl_id)
                    if product_tmpl.is_concrete_product:
                        raise ValidationError(_("You cannot create a BoM for a concrete product.\nYou must create a new version from the mix BoM associated with this concrete product."))
        return super(MrpBomConcreteProduct, self).create(vals_list)

    def button_new_version(self):
        self.ensure_one()
        if self.is_concrete_product and self.type != 'mix':
            return super(MrpBomConcreteProduct, self.with_context(archive_old_version=False)).button_new_version()
        return super(MrpBomConcreteProduct, self).button_new_version()

    def button_activate(self):
        self.ensure_one()
        result = super(MrpBomConcreteProduct, self).button_activate()
        for bom in self.filtered(lambda b: b.is_concrete_product and b.type != 'mix'):
            boms = bom._get_all_version_boms().filtered(lambda b: b != bom)
            boms.button_historical()
        return result

    def write(self, vals):
        result = super(MrpBomConcreteProduct, self).write(vals)
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
                    productions_confirmed = productions.filtered(lambda p: p.state == 'confirmed')
                    productions_confirmed._write({'state':'draft'})
                    productions_confirmed.invalidate_model(['state'])
                    productions.bom_id = last_version_bom
                    productions_confirmed._write({'state':'confirmed'})
                    productions_confirmed.invalidate_model(['state'])
        return result
