from odoo import api, fields, models, Command, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # Override bom_id field
    bom_id = fields.Many2one('mrp.bom', tracking=True)
