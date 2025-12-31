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
    
    @api.onchange('vehicle_id')
    def onchange_vehicle(self):
        self.vehicle_station_id = self.vehicle_id.station_id.id and self.vehicle_id.station_id or False
    
    def action_confirm(self):
        active_id = self.env.context.get('active_id')
        record = self.env['concrete.load'].browse(active_id)
        record.write({'vehicle_id':self.vehicle_id.id,
                      'vehicle_station_id':self.vehicle_station_id.id})
        return
