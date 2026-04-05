from odoo import models, fields, _

class ResCompany(models.Model):
    _inherit = "res.company"

    s_curve_mode = fields.Selection([
        ('month', 'Month'),
        ('week', 'Week'),
    ], default='month', help= 'This setting controls how plan lines are generated and how progress is aggregated in the S-Curve chart.')

    chart_amount_unit = fields.Selection([
        ('vnd', 'VND'),
        ('million', 'Million'),
        ('billion', 'Billion')
    ], default='billion', help='This setting only affects how values are displayed in charts and reports and does not change the original contract or financial data stored in the system.')