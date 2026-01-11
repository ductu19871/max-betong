# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    so_type = fields.Selection(
        [
            ('concrete', 'Concrete'),
            ('bom', 'Pump'),
            ('normal', 'Normal'),
        ],
        string='SO Type',
        default='normal',
        required=True,
        help='Sale Order Type\n'
             'Concrete SO: for concrete products, managed separately according to Concrete business.\n'
             'Pump SO: for concrete pumping services, managed separately according to Pump business.\n'
             'Normal SO: standard sales order, follows default Odoo flow.'
    )

    trial_mix = fields.Boolean(
        string='Trial Mix',
        default=False,
        copy=False,
        help='Mark if this Concrete order is a trial mix order. '
             'Used to distinguish trial orders from commercial orders. '
             'Allows quick filtering of trial mix orders in the order list.'
    )

    has_pump = fields.Boolean(
        string='Has Pump',
        default=False,
        copy=False,
        help='Mark if this Concrete order includes Pump service. '
             'Used to distinguish Concrete orders with and without Pump. '
             'Allows quick filtering of orders with Pump in the order list.'
    )

    related_pump_so_id = fields.Many2one(
        'sale.order',
        string='Related Pump SO',
        readonly=True,
        help='Pump order automatically created when Has Pump is checked and moved to Planned'
    )

    state = fields.Selection(selection_add=[
                    ('planned', 'Planned'),
                    ('dispatching', 'Dispatching'),
                    ('done', 'Completed'),
                ])

    dispatching_date = fields.Datetime(
        string='Dispatching Date',
        readonly=True,
        help='Time when moved to Dispatching status'
    )

    volume = fields.Float(
        string='Volume',
        compute='_compute_volume',
        help='Volume of Concrete product in the order (m³)',
        store =True
    )

    volume_allocated = fields.Float(
        string='Allocated Volume',
        compute='_compute_volume_allocated',
        help='Total volume from linked Loads (m³)',
        store =True
    )

    volume_unallocated = fields.Float(
        string='Unallocated Volume',
        compute='_compute_volume_unallocated',
        help='Volume not yet allocated to Load (m³)',
        store =True
    )

    load_ids = fields.One2many(
        'concrete.load',
        'sale_order_id',
        string='Loads',
        help='List of Loads linked to this SO'
    )
    
    count_load = fields.Integer(compute="_compute_count_load",store=True,string='Load count')
    
    ticket_ids = fields.One2many(
        'concrete.ticket',
        'sale_order_id',
        string='Ticket',
        help='List of Ticket linked to this SO'
    )
    
    concrete_station_id = fields.Many2one(
        'mrp.workcenter',
        string='Station',
        help="Concrete production station (Work Center). "
             "Each Concrete SO must be assigned to a Station for production coordination."
    )
    
    sale_concrete_id = fields.Many2one('sale.order',string='SO Concrete Origin',readonly =True)
    sale_pumb_ids = fields.One2many('sale.order','sale_concrete_id',string='Sale Pumbs')
    product_uom = fields.Many2one(related='order_line.product_uom',string='UoM',store =True)
    bom_id = fields.Many2one('mrp.bom',string='Mix',compute="compute_bom",store =True)
    mix_note = fields.Text(string='Mix Note',compute="compute_bom",store =True)
    
    @api.depends('order_line','order_line.product_id')
    def compute_bom(self):
        for so in self:
            bom_id = False
            mix_note = ''
            if so.order_line:
                product_tmpl_id = so.order_line[0].product_template_id
                if product_tmpl_id:
                    bom_mix_id = self.env['mrp.bom'].with_context(active_test=False).search([('product_tmpl_id','=',product_tmpl_id.id),
                                                             ('type','=','mix')],limit=1)
                    if bom_mix_id:
                        bom_id = bom_mix_id.id
                        mix_note = bom_mix_id.note
            so.bom_id = bom_id
            so.mix_note = mix_note
    
    @api.depends('load_ids')
    def _compute_count_load(self):
        for so in self:
            so.count_load = len(so.load_ids)
    
    @api.depends('state', 'order_line.invoice_status')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.
        """
        # apply origin logic to `normal` SO
        normal_sale_orders = self.filtered(lambda so: so.so_type != 'concrete')
        super(SaleOrder, normal_sale_orders)._compute_invoice_status()
        concrete_sale_orders = self - normal_sale_orders
        confirmed_orders = concrete_sale_orders.filtered(lambda so: so.state == 'done')
        (concrete_sale_orders - confirmed_orders).invoice_status = 'no'
        (self - confirmed_orders).invoice_status = 'no'
        if not confirmed_orders:
            return
        lines_domain = [('is_downpayment', '=', False), ('display_type', '=', False)]
        line_invoice_status_all = [
            (order.id, invoice_status)
            for order, invoice_status in self.env['sale.order.line']._read_group(
                lines_domain + [('order_id', 'in', confirmed_orders.ids)],
                ['order_id', 'invoice_status']
            )
        ]
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state not in ('sale','done'):
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                if any(invoice_status == 'no' for invoice_status in line_invoice_status):
                    # If only discount/delivery/promotion lines can be invoiced, the SO should not
                    # be invoiceable.
                    invoiceable_domain = lines_domain + [('invoice_status', '=', 'to invoice')]
                    invoiceable_lines = order.order_line.filtered_domain(invoiceable_domain)
                    special_lines = invoiceable_lines.filtered(
                        lambda sol: not sol._can_be_invoiced_alone()
                    )
                    if invoiceable_lines == special_lines:
                        order.invoice_status = 'no'
                    else:
                        order.invoice_status = 'to invoice'
                else:
                    order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'

    @api.depends('order_line', 'order_line.product_uom_qty', 'order_line.product_id', 'so_type')
    def _compute_volume(self):
        for order in self:
            if order.so_type == 'concrete':
                betong_line = order.order_line.filtered(
                    lambda l: l.product_id and l.product_id.is_concrete_product
                )
                if betong_line:
                    order.volume = betong_line[0].product_uom_qty
                else:
                    order.volume = 0.0
            else:
                order.volume = 0.0

    @api.depends('load_ids', 'load_ids.volume', 'so_type')
    def _compute_volume_allocated(self):
        """Calculate total volume from linked Loads"""
        for order in self:
            order.volume_allocated = 0.0
            if order.so_type == 'concrete':
                order.volume_allocated = sum(order.load_ids.mapped('volume'))
            else:
                order.volume_allocated = 0.0

    @api.depends('volume', 'volume_allocated', 'so_type')
    def _compute_volume_unallocated(self):
        """Calculate unallocated volume = Volume - Allocated Volume"""
        for order in self:
            if order.so_type == 'concrete':
                order.volume_unallocated = order.volume - order.volume_allocated
            else:
                order.volume_unallocated = 0.0

    @api.onchange('so_type')
    def _onchange_so_type(self):
        if self.so_type != 'concrete':
            self.trial_mix = False
            self.has_pump = False
            self.related_pump_so_id = False

    def action_cancel(self):
        for order in self:
            if order.so_type == 'concrete':
                if order.state == 'dispatching':
                    if order.ticket_ids:
                        mo = self.env['mrp.production'].search([('sale_order_id','=',order.id)])
                        mo_completed = mo.filtered(lambda m: m.state_concrete == 'completed')
                        if mo_completed:
                            raise ValidationError(_('Cannot cancel SO when there are MOs in Completed status.'))
                        mo_dump_and_remix = mo.filtered(lambda m: m.state_concrete in ['dump', 'remix'])
                        if mo_dump_and_remix:
                            raise ValidationError(_('Cannot cancel SO when there are MOs in Dump/Remix status.'))
        return super().action_cancel()
            
    def action_confirm(self):
        betong_orders = self.filtered(lambda o: o.so_type == 'concrete')
        normal_orders = self - betong_orders
        if normal_orders:
            super(SaleOrder, normal_orders).action_confirm()
        for order in betong_orders:
            order.write({
                'state': 'sale',
            })
            order.message_post(body=_('Order has been confirmed (no MO/DO generated)'))
        return True

    def action_betong_set_planned(self):
        self.write({'state':'planned'})
        for order in self:
            if order.has_pump:
                note = ''
                if order.order_line:
                    note = f"{order.order_line[0].product_id.name} : {order.order_line[0].product_uom_qty} {order.order_line[0].product_uom.name}"
                order.copy(default={"sale_concrete_id": order.id,
                                    "order_line":[],
                                    "note":note,
                                    "so_type":'bom'})

    def action_betong_set_completed(self):
        self.write({'state':'done'})
    
    def action_betong_set_dispatching(self):
        self.write({'state':'dispatching'})

    def action_cancel(self):
        for order in self:
            if order.so_type != 'concrete':
                continue
            if order.state == 'dispatching':
                if order.ticket_ids:
                    completed_tickets = order.ticket_ids.filtered(lambda t: t.state == 'completed')
                    if completed_tickets:
                        raise ValidationError(_('Cannot cancel SO when there are tickets in Completed status.'))
                    valid_states = ['dum', 'remix_swapped']
                    if not all(t.state in valid_states for t in order.ticket_ids):
                        raise ValidationError(_('Can only cancel SO when all tickets are in Dum/Remix&Swapped status.'))
        return super().action_cancel()


    def _check_ticket_loading_and_update_state(self):
        """Check tickets and auto-transition to Dispatching if there's a Loading ticket"""
        for order in self:
            if order.so_type != 'concrete' or order.state != 'planned':
                continue
            loading_tickets = order.ticket_ids.filtered(lambda t: t.state == 'loading')
            if loading_tickets:
                order.state = 'dispatching'
                order.dispatching_date = fields.Datetime.now()
                
    def action_split_load(self):
        for order in self:
            fixed_load_qty = self.company_id.concrete_load_volume
            if fixed_load_qty <= 0:
                raise ValidationError(_('Concrete load volume must be greater than 0.'))
            # Tính toán dựa trên volume_unallocated hiện tại
            remaining_qty = order.volume_unallocated
            if remaining_qty <= 0:
                return
            # Sử dụng floor division để tránh lỗi làm tròn
            full_load_count = int(remaining_qty // fixed_load_qty)
            remainder_qty = remaining_qty - (full_load_count * fixed_load_qty)
            load_obj = self.env['concrete.load']
            # Tạo các load đầy
            for i in range(full_load_count):
                load_obj.create(order._prepare_load_vals(fixed_load_qty))
            # Chỉ tạo load còn lại nếu số lượng > 0 (và đủ lớn, tránh lỗi làm tròn)
            if remainder_qty > 0.001:  # Tránh lỗi làm tròn số float
                load_obj.create(order._prepare_load_vals(remainder_qty))
    
    def _prepare_load_vals(self, quantity):
        order_line = self.order_line.filtered(lambda l: not l.display_type)[:1]
        product = order_line.product_id
        # mix_note = ''
        # bom = self.env['mrp.bom']._bom_find(products=product).get(product)
        # if bom:
        #     mix_note = bom.note or ''
        return {
            'volume': quantity,
            'sale_order_id': self.id,
            'product_id': product.id,
            'load_station_id': self.concrete_station_id.id,
            'delivery_address_id': self.partner_shipping_id.id,
            'company_id':self.company_id.id,
        }
    
    def action_view_load(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Loads',
            'res_model': 'concrete.load',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.load_ids.ids)],
        }
    
    def action_view_so_pumb(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.sale_pumb_ids.ids)],
        }
    
    def action_view_so_origin(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.sale_concrete_id.ids)],
        }
    
    
    @api.constrains('order_line')
    def _check_line_concrete(self):
        for rec in self:
            if rec.so_type =='concrete' and len(rec.order_line) > 1:
                raise ValidationError(_('Do not create two products in this type of concrete.'))
    
    @api.constrains('volume_unallocated')
    def _check_volume_unallocated(self):
        for rec in self:
            if rec.volume_unallocated < 0:
                raise ValidationError(_('volume unallocated must be greater than 0.'))
    
    
    
    
    
    
    
    
    
    
    


