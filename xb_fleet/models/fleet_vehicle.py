import datetime

from odoo import fields, models, api
from datetime import date, timedelta


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    ref = fields.Char(string="Ref", tracking=True)
    depriciation_method_number = fields.Integer(
        string="Depriciation Method Number", tracking=True
    )
    depriciation_method_period = fields.Selection(
        [("month", "Month"), ("year", "Year")],
        default="month",
        string="Depriciation Method Period",
        tracking=True,
    )
    fuel_limit_value = fields.Float(string="Fuel Limit Value", tracking=True)
    fuel_limit_type = fields.Selection(
        [("km", "l/km"), ("ca", "l/ca"), ("hour", "l/hour")],
        default="km",
        string="Fuel Limit Type",
        tracking=True,
    )

    document_ids = fields.Many2many("ir.attachment", string="Documents")
    brand_name = fields.Char("Brand Name", tracking=True)
    is_error = fields.Boolean(string="Is Error")
    error_select = fields.Selection(
        [("blocked", "Error"), ("none", "None")], string="Error", default="none", tracking=True
    )

    _sql_constraints = [
        (
            'uniq_license_plate',
            'unique(license_plate)',
            'The license plate already exists.'
        ), (
            'uniq_ref',
            'unique(ref)',
            'The reference number already exists.'
        ),
    ]

    def action_error(self):
        self.update({"error_select": "blocked"})

    def action_non_error(self):
        self.update({"error_select": "none"})
