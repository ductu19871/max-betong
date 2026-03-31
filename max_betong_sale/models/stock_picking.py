# -*- coding: utf-8 -*-
# stock_picking.py
from odoo import models, fields, api,_
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
        string='Factory out time',
        tracking=True,
        copy=False,
    )
    factory_out_time_manual = fields.Boolean(
        string='Factory Out Time Manual',
        default=False,
        copy=False,
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
    
    state_raw = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], compute='_compute_state_raw', string="Status", store=True)

    @api.onchange('ticket_id')
    def _onchange_ticket_id_factory_out_time(self):
        if self.ticket_id and not self.factory_out_time_manual:
            self.factory_out_time = self.ticket_id.loaded_datetime

    @api.depends('state')
    def _compute_state_raw(self):
        for rec in self:
            rec.state_raw = rec.state

    @api.depends('sale_id.order_line.qty_delivered','move_ids_without_package.product_uom_qty', 'state')
    def _compute_accumulated_qty(self):
        for picking in self:
            total = 0.0
            if picking.sale_id:
                for line in picking.sale_id.order_line:
                    total += line.qty_delivered
            # Get product quantity on DO Lines
            if picking.move_line_ids:
                total += sum(picking.move_ids_without_package.mapped(lambda x: x.product_uom_qty if x.state != 'done' else 0.0)) or 0.0
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

    def _sync_factory_out_time_from_ticket(self):
        for picking in self.filtered(lambda p: p.ticket_id and not p.factory_out_time_manual):
            new_value = picking.ticket_id.loaded_datetime or False
            if picking.factory_out_time != new_value:
                picking.with_context(skip_factory_out_time_manual=True).write({
                    'factory_out_time': new_value,
                })

    def action_open_factory_out_time_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Update Factory Out Time'),
            'res_model': 'stock.picking.factory.out.time.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_factory_out_time': self.factory_out_time,
            }
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if (
                    vals.get('ticket_id')
                    and not vals.get('factory_out_time')
                    and not vals.get('factory_out_time_manual')
            ):
                ticket = self.env['mrp.production'].browse(vals['ticket_id'])
                if ticket:
                    vals['factory_out_time'] = ticket.loaded_datetime
        return super(StockPicking, self).create(vals_list)

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if 'ticket_id' in vals:
            self.filtered(lambda p: not p.factory_out_time_manual)._sync_factory_out_time_from_ticket()
        return res
