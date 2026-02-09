# -*- coding: utf-8 -*-
from odoo import models, fields,api

class WizardConfirmFields(models.TransientModel):
    _name = 'wizard.confirm.fields'
    _description = 'Confirm Selection'

    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
    )

    vehicle_station_id = fields.Many2one(
        'mrp.workcenter',
        string='Vehicle Station',
    )
    
    load_station_id = fields.Many2one(
        'mrp.workcenter',
        string='Load Station',
    )
    
    volume = fields.Float(
        string='Volume',
        help="Load volume must be greater than 0.",
    )
    
    def action_assign_ticket(self):
        active_id = self.env.context.get('active_id')
        record = self.env['concrete.load'].browse(active_id)
        record.write({'vehicle_id':self.vehicle_id.id,
                      'vehicle_station_id':self.vehicle_station_id.id})
        record.action_assign_ticket()
        return
    
    def action_confirm_volumn(self):
        active_id = self.env.context.get('active_id')
        record = self.env['concrete.load'].browse(active_id)
        record.write({'load_station_id':self.load_station_id.id,
                      'volume':self.volume})
        return
