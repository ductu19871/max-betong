from odoo import models, fields, api

class PaperFormat(models.Model):
    _inherit = "report.paperformat"

    enable_forms = fields.Boolean('Enable PDF Forms')