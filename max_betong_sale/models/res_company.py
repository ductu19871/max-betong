import psycopg2
import json
from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    concrete_load_volume = fields.Float('Concrete Load Volume')
