# -*- coding: utf-8 -*-
# stock_picking.py
from odoo import models, fields, api
import datetime
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    do_type = fields.Selection(
        [
            ('concrete', 'Concrete'),
            ('normal', 'Normal'),
        ],
        compute='_compute_do_type',
        store=True
    )
    ticket_id = fields.Many2one(
        'mrp.production',
        string='Ticket',
        readonly=True
    )
    factory_out_time = fields.Datetime(
        related="ticket_id.loaded_datetime",
        string='Factory out time',
        store=True
    )
    accumulated_qty = fields.Float(
        string='Accumulated Delivered Quantity',
        compute='_compute_accumulated_qty',
        store =True,
        help='The accumulated delivered quantity is the total quantity that has been delivered for the related Sales Order (SO) up to the current time.'
    )
    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        related='ticket_id.vehicle_station_id',
        readonly=True
    )
    
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        related='ticket_id.vehicle_id',
        readonly=True
    )
    
    driver_id = fields.Many2one(
        'res.partner',
        related='vehicle_id.driver_id',
        readonly=True
    )
    
    @api.depends('sale_id','sale_id.order_line')
    def _compute_accumulated_qty(self):
        for picking in self:
            total = 0.0
            if picking.sale_id:
                for line in picking.sale_id.order_line:
                    total += line.qty_delivered
            picking.accumulated_qty = total
    
    @api.depends('sale_id.so_type')
    def _compute_do_type(self):
        for picking in self:
            picking.do_type = (
                'concrete'
                if picking.sale_id and picking.sale_id.so_type == 'concrete'
                else 'normal'
            )
            
    def get_partner_address(self):
        partner = self.partner_id
        address = [
            partner.street,
            partner.street2,
            partner.city,
            partner.state_id.name if partner.state_id else None,
            partner.zip,
            partner.country_id.name if partner.country_id else None,
        ]
    
        return ', '.join(filter(None, address))
    
    def convert_date(self, date):
        if not date:
            return ''
        date = datetime.datetime.strptime(str(date.date()), DATE_FORMAT)
        return date.strftime('%d/%m/%Y')
    
    def convert_time(self, date):
        if not date:
            return ''
        date = date + datetime.timedelta(hours=7)
        # date = datetime.datetime.strptime(str(date), DATETIME_FORMAT)
        return date.strftime('%H:%M:%S')
    
    def get_qty_done(self):
        return self.convert_number(sum(self.move_ids.mapped('quantity')))
    
    def convert_number(self,quantity):
        x_quantity = "{:_.2f}".format(quantity).replace('.', ',').replace('_', '.')
        return x_quantity
    
    def button_validate(self):
        res = super().button_validate()
        self._compute_accumulated_qty()
        return res
    
    
    
    