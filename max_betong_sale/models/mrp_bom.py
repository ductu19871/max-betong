# -*- coding: utf-8 -*-
from odoo import _, models,fields, api
from odoo.tools import float_round
from datetime import date

class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    
    note = fields.Text()
    type = fields.Selection(selection_add=[('mix','Mix')],ondelete={'mix': 'set default'})

    
    
    
    
    