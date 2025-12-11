# -*- coding: utf-8 -*-
from odoo import models, fields

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    vehicle_type = fields.Selection(related='model_id.vehicle_type',help=(
            "Vehicle classification.\n"
            "Concrete Truck: used for transporting concrete, managed separately based on concrete logistics.\n"
            "Pump Truck: used for concrete pumping services, managed separately based on pump operations.\n"
            "Standard Vehicle: normal vehicle following the default workflow."
        ))
    station_id = fields.Many2one(
        'mrp.workcenter',
        string='Station',
        help=(
            "The station to which the vehicle belongs.\n"
            "Used to determine the batching plant when the vehicle participates in concrete delivery."
        )
    )
