from odoo import _, models,fields, api, Command
from odoo.tools import float_round
from datetime import date,timedelta
from odoo.exceptions import UserError, ValidationError

state_to_datetime_field = {
                'assigned': 'assigned_datetime',
                'loading': 'loading_datetime',
                'loaded': 'loaded_datetime',
                'leave': 'leave_datetime',
                'arrived': 'arrived_state_tracking_datetime',
                'unloading': 'unloading_state_tracking_datetime',
                'return': 'return_state_tracking_datetime',
                'completed': 'completed_state_tracking_datetime',
            }

class Production(models.Model):
    _inherit = 'mrp.production'
    
    mo_type = fields.Selection(
        [
            ('concrete', 'Concrete'),
            ('normal', 'Normal'),
        ],
        string='MO Type',
        default='normal',
        required=True,
    )
    load_id = fields.Many2one('concrete.load',string='Concrete Load',ondelete="set null")
    load_station_id = fields.Many2one('mrp.workcenter', string='Load Station', related='load_id.load_station_id', readonly=True, store=True)
    bom_mix_id = fields.Many2one('mrp.bom', string='BoM Mix', related='load_id.bom_id', readonly=True)
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        compute='_compute_vehicle_id',
        string='Vehicle',
        store =True,
        readonly=False
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
        'mrp.workcenter',
        compute='_compute_vehicle_station_id',
        string='Vehicle Station',
        help="Station associated with the selected vehicle. "
             "Automatically filled based on vehicle configuration.",
        store =True,
        readonly=True
    )
    
    state_concrete = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('assigned', 'Assigned'),
            ('loading', 'Loading'),
            ('loaded', 'Loaded'),
            ('leave', 'Leave'),
            ('arrived', 'Arrived'),
            ('unloading', 'Unloading'),
            ('return', 'Return'),
            ('completed', 'Completed'),
            ('on_hold', 'On Hold'),
            ('dump', 'Dump'),
            ('remix', 'Remix'),
            ('swap', 'Swap'),
            ('cancel', 'Canceled'),
        ],
        string='Concrete State',
        default="draft",
        tracking=True,
        copy=False
    )
    
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
    
    arrived_state_tracking_datetime = fields.Datetime(
        string='Arrived State Tracking Time',
        readonly=True
    )
    unloading_state_tracking_datetime = fields.Datetime(
        string='Unloading State Tracking Time',
        readonly=True
    )
    return_state_tracking_datetime = fields.Datetime(
        string='Return State Tracking Time',
        readonly=True
    )
    completed_state_tracking_datetime = fields.Datetime(
        string='Completed State Tracking Time',
        readonly=True
    )
    
    incident_datetime = fields.Datetime(
        string='Incident Recording Time',
        readonly=True,
        help='Time when ticket is on hold or completed (for analytics tracking)'
    )
    
    distance_km = fields.Float(
        string='Distance (km)',
        help='Distance from plant to site'
    )
    eta = fields.Datetime(compute="_compute_eta",string='ETA',store =True)
    
    do_ids = fields.One2many('stock.picking','ticket_id',string='Do')
    do_count = fields.Integer(compute='_compute_do_count',store =True)

    ticket_on_hold_type = fields.Selection(
        selection=[
            ('remix', 'Remix'),
            ('swap', 'Swap'),
        ],
        string='Ticket On Hold Type'
    )
    ticket_on_hold_id = fields.Many2one(
        'mrp.production',
        string='Ticket On Hold',
        help='Reference to the production ticket that is put on hold',
        readonly=True,
        copy=False,
        store=True
    )
    on_hold_ticket_id = fields.Many2one(
        'mrp.production',
        string='On Hold Ticket',
        help='Reference to the ticket that is currently on hold for this operation',
        readonly=True,
        copy=False,
        store=True
    )
    on_hold_reason = fields.Text(string='On Hold Reason', copy=False)

    ticket_on_hold_reason = fields.Text(related='ticket_on_hold_id.on_hold_reason', string='Ticket On Hold Reason', readonly=False)
    on_hold_ticket_type = fields.Selection(related='on_hold_ticket_id.ticket_on_hold_type')
    is_invisible_dashboard = fields.Boolean(string="Invisible Dashboard")
    ticket_note = fields.Text()
    partner_id = fields.Many2one(
        related="sale_order_id.partner_id",
        store=True,
    )
    driver_id = fields.Many2one(
        related="vehicle_id.driver_id",
        store=True,
    )
    load_bom_id = fields.Many2one(related='load_id.bom_id', string="Load BOM")
    late_minutes = fields.Integer(
        string='Late (minutes)',
        compute='_compute_eta_status',
        store=True,
        readonly=True,
    )
    is_on_time = fields.Boolean('On time', compute='_compute_eta_status',
        store=True)
    is_late = fields.Boolean('Late', compute='_compute_eta_status',
        store=True)
    
    waiting_at_plant_minutes = fields.Float(
        string='Waiting at Plant (min)',
        compute='_compute_cycle_times',
        store=True
        )

    trip_cycle_time_minutes = fields.Float(
        string='Trip Cycle Time (min)',
        compute='_compute_cycle_times',
        store=True
        )   

    full_cycle_time_minutes = fields.Float(
        string='Full Cycle Time (min)',
        compute='_compute_cycle_times',
        store=True
        )
    # concrete_lifespan

    lifetime_minutes = fields.Float(
        string="Lifetime (minutes)",
        compute="_compute_lifetime",
        store=True
    )

    @api.depends('loaded_datetime', 'return_state_tracking_datetime')
    def _compute_lifetime(self):
        for rec in self:
            if rec.loaded_datetime and rec.return_state_tracking_datetime:
                delta = rec.return_state_tracking_datetime - rec.loaded_datetime
                minutes = delta.total_seconds() / 60
                rec.lifetime_minutes = minutes if minutes > 0 else 0
            else:
                rec.lifetime_minutes = 0

    @api.constrains('ticket_on_hold_type', 'ticket_on_hold_id')
    def _check_ticket_on_hold_type(self):
        for mo in self:
            if mo.ticket_on_hold_type and not mo.ticket_on_hold_id:
                raise ValidationError(_("Ticket on hold type is set but ticket on hold is not set."))
            if not mo.ticket_on_hold_type and mo.ticket_on_hold_id:
                raise ValidationError(_("Ticket on hold type is not set but ticket on hold is set."))

    @api.constrains('load_station_id', 'vehicle_station_id')
    def _check_station_concrete_load(self):
        for mo in self.filtered(lambda mo: mo.load_station_id and mo.vehicle_station_id):
            if mo.load_station_id != mo.vehicle_station_id:
                raise UserError(_("Load station and vehicle station are not consistent."))

    @api.onchange('load_id')
    def _onchange_load_id(self):
        for mo in self.filtered('load_id'):
            vals = mo.load_id._prepare_ticket_vals()
            vals.pop('bom_id', None)
            vals.pop('vehicle_id', None)
            vals.pop('vehicle_station_id', None)
            for field, value in vals.items():
                setattr(mo, field, value)

    def _onchange_product_id(self):
        remix_tickets = self.filtered(lambda mo: mo.ticket_on_hold_id)
        super(Production, self - remix_tickets)._onchange_product_id()

    def _onchange_producing(self):
        remix_tickets = self.filtered(lambda mo: mo.ticket_on_hold_id)
        super(Production, self - remix_tickets)._onchange_producing()

    @api.depends('ticket_on_hold_id', 'load_id')
    def _compute_vehicle_id(self):
        for mo in self:
            if remix_ticket := mo.ticket_on_hold_id:
                mo.vehicle_id = remix_ticket.vehicle_id
            elif load := mo.load_id:
                mo.vehicle_id = load.vehicle_id

    @api.depends('ticket_on_hold_id', 'load_id', 'vehicle_id')
    def _compute_vehicle_station_id(self):
        for mo in self:
            if remix_ticket := mo.ticket_on_hold_id:
                mo.vehicle_station_id = remix_ticket.vehicle_station_id
            else:
                mo.vehicle_station_id = mo.load_id.vehicle_station_id or mo.vehicle_id.station_id

    def _compute_move_raw_ids(self):
        remix_tickets = self.filtered(lambda mo: mo.ticket_on_hold_id)
        for mo in remix_tickets:
            if not mo.move_raw_ids.filtered(lambda m: m.ticket_on_hold_id == mo.ticket_on_hold_id):
                values = mo._get_move_raw_values(
                    mo.ticket_on_hold_id.product_id,
                    mo.ticket_on_hold_id.product_qty,
                    mo.ticket_on_hold_id.product_uom_id,
                )
                values['ticket_on_hold_id'] = mo.ticket_on_hold_id.id
                mo.move_raw_ids = [Command.link(m.id) for m in mo.move_raw_ids] + [Command.create(values)]
        super(Production, self - remix_tickets)._compute_move_raw_ids()

    def _compute_bom_id(self):
        remix_tickets = self.filtered(lambda mo: mo.ticket_on_hold_id)
        super(Production, self - remix_tickets)._compute_bom_id()

    @api.depends('load_id')
    def _compute_product_qty(self):
        productions_load = self.filtered('load_id')
        super(Production, self - productions_load)._compute_product_qty()
        for mo in productions_load:
            mo.product_qty = mo.load_id.volume

    @api.depends('eta', 'arrived_state_tracking_datetime')
    def _compute_eta_status(self):
        for rec in self:
            if rec.eta and rec.arrived_state_tracking_datetime:
                delta = (rec.arrived_state_tracking_datetime - rec.eta).total_seconds() / 60
                if delta > 0:
                    rec.late_minutes = int(delta)
                    rec.is_on_time = False
                    rec.is_late = True
                else:
                    rec.late_minutes = 0
                    rec.is_on_time = True
                    rec.is_late = False
            else:
                rec.late_minutes = 0
                rec.is_on_time = False
                rec.is_late = False

    def _compute_cycle_times(self):
        for rec in self:
            if rec.loading_datetime and rec.leave_datetime:
                rec.waiting_at_plant_minutes = (
                    (rec.leave_datetime - rec.loading_datetime).total_seconds() / 60
                )
            else:
                rec.waiting_at_plant_minutes = 0

            if rec.leave_datetime and rec.completed_state_tracking_datetime:
                rec.trip_cycle_time_minutes = (
                    (rec.completed_state_tracking_datetime - rec.leave_datetime).total_seconds() / 60
                )
            else:
                rec.trip_cycle_time_minutes = 0

            if rec.loading_datetime and rec.completed_state_tracking_datetime:
                rec.full_cycle_time_minutes = (
                    (rec.completed_state_tracking_datetime - rec.loading_datetime).total_seconds() / 60
                )
            else:
                rec.full_cycle_time_minutes = 0
    
    def action_view_do(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Delivery Orders',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('ticket_id', '=', self.id)],
        }
    
    @api.depends('do_ids')
    def _compute_do_count(self):
        for mo in self:
            mo.do_count = len(mo.do_ids)
    
    def action_loading(self):
        self.write({'loading_datetime':fields.Datetime.now(),
                   'state_concrete':'loading'})
        self.vehicle_id.write({'state_concrete':'loading'})
        self.sale_order_id.action_betong_set_dispatching()
    
    def action_loaded(self):
        self.write({'loaded_datetime':fields.Datetime.now(),
                   'state_concrete':'loaded'})
        self.vehicle_id.write({'state_concrete':'loaded'})
        
    def action_leave(self):
        self.write({'leave_datetime':fields.Datetime.now(),
                   'state_concrete':'leave'})

    def action_confirm(self):
        res = super().action_confirm()
        self.write({'assigned_datetime':fields.Datetime.now()})
        self.filtered(lambda t: t.ticket_on_hold_type == 'remix').ticket_on_hold_id.state_concrete = 'remix'
        self.filtered(lambda t: t.ticket_on_hold_type == 'swap').ticket_on_hold_id.state_concrete = 'swap'
        self.load_id.filtered(lambda l: l.state != 'completed').action_set_completed()
        self.ticket_on_hold_id.do_ids.filtered(lambda p: p.state != 'cancel').action_cancel()
        for ticket in self.filtered(lambda t: t.load_id and not t.do_ids):
            ticket.load_id._create_delivery_order(ticket)
        return res

    def action_open_concrete_ticket_form(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('max_betong_sale.action_concrete_ticket')
        action['views'] = [(False, 'form')]
        action['res_id'] = self.id
        return action

    def action_on_hold(self):
        self.write({'state_concrete':'on_hold'})
        self.vehicle_id.write({'state_concrete':'on_hold'})

    def action_concrete_remix(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id('max_betong_sale.action_concrete_ticket')
        action['name'] = 'Concrete Remix'
        action['context'] = {
            'default_mo_type': 'concrete',
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_ticket_on_hold_id': self.id,
            'default_ticket_on_hold_type': 'remix',
            'default_load_id': self.load_id.id,
            'default_product_id': self.product_id.id
        }
        action['views'] = [(self.env.ref('max_betong_sale.mrp_production_ticket_on_hold_wizard_view').id, 'form')]
        action['target'] = 'new'
        return action

    def action_concrete_swap(self):
        self.ensure_one()
        action = self.action_concrete_remix()
        action['name'] = 'Concrete Swap'
        action['context']['default_ticket_on_hold_type'] = 'swap'
        return action

    def action_view_on_hold_ticket(self):
        if not self.on_hold_ticket_id:
            raise ValidationError(_("No on hold ticket found."))
        action = self.env["ir.actions.actions"]._for_xml_id('max_betong_sale.action_concrete_ticket')
        action['views'] = [(False, 'form')]
        action['res_id'] = self.on_hold_ticket_id.id
        return action

    def action_view_ticket_on_hold(self):
        if not self.ticket_on_hold_id:
            raise ValidationError(_("No ticket on hold found."))
        action = self.env["ir.actions.actions"]._for_xml_id('max_betong_sale.action_concrete_ticket')
        action['views'] = [(False, 'form')]
        action['res_id'] = self.ticket_on_hold_id.id
        return action

    # NOT USED
    def action_swap(self):
        self.write({'state_concrete': 'swap'})

    def _get_avg_mixing_time(self):
        tickets = self.search([
            ('mo_type', '=', 'concrete'),
            ('state_concrete', '=', 'completed'),
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
            ('mo_type', '=', 'concrete'),
            ('state_concrete', '=', 'completed'),
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
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.get_name_sequene()
        new_tickets = super().create(vals_list)
        for ticket in new_tickets:
            if ticket.ticket_on_hold_id:
                ticket.ticket_on_hold_id.on_hold_ticket_id = ticket
        return new_tickets
    
    def get_name_sequene(self, today=None):
        today = today or fields.Date.context_today(self)
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

        return seq

    def write(self, vals):
        res = super().write(vals)
        if 'state_concrete' in vals:
            for record in self.filtered(lambda r: r.mo_type == 'concrete'):
                new_state = record.state_concrete
                datetime_field = state_to_datetime_field.get(new_state)
                if datetime_field and not getattr(record, datetime_field):
                    record.write({
                        datetime_field: fields.Datetime.now()
                    })
                if new_state in ('on_hold', 'completed', 'dump', 'remix', 'swap'):
                    if not record.incident_datetime:
                        record.write({
                            'incident_datetime': fields.Datetime.now()
                        })
        if 'state' in vals:
            for record in self:
                record.update_state_concrete()
        return res
    
    def update_state_concrete(self):
        if self.state =='confirmed':
            self.state_concrete = 'assigned'
            self.vehicle_id.state_concrete='assigned'
        if self.state =='progress':
            self.action_loading()
            self.vehicle_id.state_concrete='loading'
        if self.state =='done':
            self.action_loaded()
            self.vehicle_id.state_concrete='loaded'
        if self.state == 'loading':
            self.sale_order_id.state = 'dispatching'
    
    def action_cancel(self):
        res = super().action_cancel()
        self.write({'state_concrete': 'cancel'})
        return res
    
    
    
    
    
    