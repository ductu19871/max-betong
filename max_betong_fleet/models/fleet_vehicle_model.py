# -*- coding: utf-8 -*-
from odoo import models, fields

class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    vehicle_type = fields.Selection([('car', 'Car'),
                                     ('bike', 'Bike'),
                                     ('concrete', 'Concrete'),
                                     ('pump', 'Pump')], default='car', required=True)
