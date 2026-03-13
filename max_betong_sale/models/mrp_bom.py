# -*- coding: utf-8 -*-
from odoo import _, models,fields, api
from odoo.tools import float_round
from datetime import date

class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    
    note = fields.Text()
    type = fields.Selection(selection_add=[('mix','Mix')],ondelete={'mix': 'set default'})

    @api.onchange('workcenter_id')
    def _onchange_wc_id(self):
        self.picking_type_id = self.env['stock.picking.type'].search([('code','=','mrp_operation'), ('warehouse_id','=',self.workcenter_id.warehouse_id.id)])
    
    
    
    
    