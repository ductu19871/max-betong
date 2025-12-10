# -*- coding: utf-8 -*-
from odoo import models, fields

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    type = fields.Selection(
        [
            ('concrete', 'Concrete'),
            ('pump', 'Pump'),
            ('normal', 'Standard'),
        ],
        string='Vehicle Type',
        default='normal',
        required=True,
        help=(
            "Vehicle classification.\n"
            "Concrete Truck: used for transporting concrete, managed separately based on concrete logistics.\n"
            "Pump Truck: used for concrete pumping services, managed separately based on pump operations.\n"
            "Standard Vehicle: normal vehicle following the default workflow."
        )
    )
    station_id = fields.Many2one(
        'mrp.workcenter',
        string='Station',
        required=True,
        help=(
            "The station to which the vehicle belongs.\n"
            "Used to determine the batching plant when the vehicle participates in concrete delivery."
        )
    )
