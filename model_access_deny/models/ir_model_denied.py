from odoo import models, fields, api

class IrModelDenied(models.Model):
    _name = 'ir.model.denied'
    _description = 'Model Denied Access'

    name = fields.Char(required=True)
    model_id = fields.Many2one('ir.model', required=True, ondelete='cascade')
    group_id = fields.Many2one('res.groups')

    perm_read = fields.Boolean()
    perm_write = fields.Boolean()
    perm_create = fields.Boolean()
    perm_unlink = fields.Boolean()

    active = fields.Boolean(default=True)

    # def _clear_cache(self):
    #     self.env['ir.model.access']._get_allowed_models.clear_cache(
    #         self.env['ir.model.access']
    #     )

    # @api.model_create_multi
    # def create(self, vals):
    #     res = super().create(vals)
    #     self._clear_cache()
    #     return res

    # def write(self, vals):
    #     res = super().write(vals)
    #     self._clear_cache()
    #     return res

    # def unlink(self):
    #     res = super().unlink()
    #     self._clear_cache()
    #     return res
