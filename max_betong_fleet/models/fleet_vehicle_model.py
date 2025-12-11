# -*- coding: utf-8 -*-
from odoo import models, fields

class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    vehicle_type = fields.Selection(selection_add=[
                                     ('concrete', 'Concrete'),
                                     ('pump', 'Pump')],ondelete={'concrete': 'set default', 'pump': 'set default'})
