# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ConcreteLoad(models.Model):
    _inherit = 'concrete.load'

    def _get_boms_assign_ticket(self):
        boms = super(ConcreteLoad, self)._get_boms_assign_ticket()
        if load_station := self.load_station_id:
            boms = boms.filtered_domain([('workcenter_id', '=', load_station.id)])
        return boms
