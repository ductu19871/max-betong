import json
import pytz
from datetime import time, datetime

from odoo import models, fields


class FleetVehicleOdo(models.Model):
    _inherit = "fleet.vehicle.odometer"

    door_open_count = fields.Integer("Door Open Count")
    over_speed_count = fields.Integer("Over Speed Count")
    max_speed = fields.Integer("Max Speed")
    first_acc_on_time = fields.Datetime("First ACC-ON Time")
    last_acc_off_time = fields.Datetime("Last ACC-ON Time")
    acc_time = fields.Float("ACC-ON Time (s)")
    run_time = fields.Float("Run Time (s)")
    idle_time = fields.Float("Idle Time (s)")
    stop_time = fields.Float("Stop Time (s)")
    sensor_time = fields.Float("Sensor Time (s)")
    sensor_off_time = fields.Float("Sensor Off Time (s)")
    off_time = fields.Float("Off Time (s)")
    sys_time = fields.Datetime("Sys Time")
    hash_status = fields.Char(string="Hash Status")
    source = fields.Char(string="Source")
