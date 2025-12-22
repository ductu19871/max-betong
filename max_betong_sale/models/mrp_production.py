from odoo import _, models,fields, api
from odoo.tools import float_round
from datetime import date,timedelta

class Production(models.Model):
    _inherit = 'mrp.production'
    
    load_id = fields.Many2one('concrete.load',string='Concrete Load',ondelete="set null")
    vehicle_id = fields.Many2one(
        related="load_id.vehicle_id",
        string='Vehicle',
        store =True
    )
    sale_order_id = fields.Many2one(
        related="load_id.sale_order_id",
        string='SO',
        store=True,
    )
    mix_note = fields.Text(related='load_id.mix_note',string='Mix Note',store =True,
                           help="Mixing note obtained from the Bill of Materials of the product.")
    delivery_address_id = fields.Many2one(
        related="sale_order_id.partner_shipping_id",
        string='Construction Site Address',
        store=True,
    )
    vehicle_station_id = fields.Many2one(
        related='load_id.vehicle_station_id',
        string='Vehicle Station',
        help="Station associated with the selected vehicle. "
             "Automatically filled based on vehicle configuration.",
        store =True
    )
    
    state = fields.Selection(selection_add=[
        ('loading', 'Loading'),
        ('loaded', 'Loaded'),
        ('leave', 'Leave'),
        ('arrived', 'Arrived'),
        ('unloading', 'Unloading'),
        ('return', 'Return'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('dump', 'Dump'),
        ('remix', 'Remix & Swapped'),
    ])
    
    assigned_datetime = fields.Datetime(
        string='Assigned Time',
        readonly=True
    )
    loading_datetime = fields.Datetime(
        string='Loading Time',
        readonly=True
    )
    loaded_datetime = fields.Datetime(
        string='Loaded Time',
        readonly=True
    )
    leave_datetime = fields.Datetime(
        string='Leave Time',
        readonly=True
    )
    
    distance_km = fields.Float(
        string='Distance (km)',
        help='Distance from plant to site'
    )
    eta = fields.Datetime(compute="_compute_eta",string='ETA',store =True)
    
    def action_loading(self):
        self.write({'loading_datetime':fields.Datetime.now(),
                   'state':'loading'})
    
    def action_loaded(self):
        self.write({'loaded_datetime':fields.Datetime.now(),
                   'state':'loaded'})
        
    def action_leave(self):
        self.write({'leave_datetime':fields.Datetime.now(),
                   'state':'leave'})
    
    def action_confirm(self):
        res = super().action_confirm()
        for ticket in self:
            ticket.assigned_datetime = fields.Datetime.now()
        return res
            
    def action_on_hold(self):
        self.write({'state':'on_hold'})
    
    def _get_avg_mixing_time(self):
        tickets = self.search([
            ('state', '=', 'completed'),
            ('loading_datetime', '!=', False),
            ('loaded_datetime', '!=', False),
        ])
    
        if not tickets:
            return 0
    
        total_seconds = sum(
            (t.loaded_datetime - t.loading_datetime).total_seconds()
            for t in tickets
        )
        return total_seconds / len(tickets)
    
    def _get_avg_waiting_time(self, avg_mixing_time):
        tickets = self.search([
            ('state', '=', 'completed'),
            ('assigned_datetime', '!=', False),
            ('leave_datetime', '!=', False),
        ])
    
        if not tickets:
            return 0
    
        total_seconds = 0
        for t in tickets:
            total_seconds += (
                (t.leave_datetime - t.assigned_datetime).total_seconds()
                - avg_mixing_time
            )
    
        return max(total_seconds / len(tickets), 0)
    
    def _get_travel_time(self):
        if not self.distance_km:
            return 0
        return (self.distance_km / 40) * 3600
    
    @api.depends(
        'assigned_datetime',
        'distance_km'
    )
    def _compute_eta(self):
        for ticket in self:
            if not ticket.assigned_datetime:
                ticket.eta = False
                continue
            mixing_time = ticket._get_avg_mixing_time()
            waiting_time = ticket._get_avg_waiting_time(mixing_time)
            travel_time = ticket._get_travel_time()
    
            total_seconds = mixing_time + waiting_time + travel_time
    
            ticket.eta = ticket.assigned_datetime + timedelta(
                seconds=total_seconds
            )
    
    @api.model
    def create(self, vals):
        today = fields.Date.context_today(self)
        date_str = today.strftime('%Y%m%d')
        seq = self.env['ir.sequence'].next_by_code(
            f'mrp.production.ticket.{date_str}'
        )
        if not seq:
            self.env['ir.sequence'].create({
                'name': f'Ticket {date_str}',
                'code': f'mrp.production.ticket.{date_str}',
                'prefix': f'T{date_str}-',
                'padding': 3,
                'number_next': 1,
            })
            seq = self.env['ir.sequence'].next_by_code(
                f'mrp.production.ticket.{date_str}'
            )
        vals['name'] = seq
        return super().create(vals)
    
    