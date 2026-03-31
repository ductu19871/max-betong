from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    s_curve_mode = fields.Selection([
        ('month', 'Month'),
        ('week', 'Week'),
    ], default='month')

    chart_amount_unit = fields.Selection([
        ('vnd', 'VND'),
        ('million', 'Million'),
        ('billion', 'Billion')
    ], default='billion')