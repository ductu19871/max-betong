from odoo import models, fields, api, _

class ChangeProductionQty(models.TransientModel):
    _inherit = 'change.production.qty'  

    mo_type = fields.Selection(related='mo_id.mo_type')