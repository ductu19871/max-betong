# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, time


class ConcreteLoad(models.Model):
    _name = 'concrete.load'
    _description = 'Concrete Load'
    _order = 'create_date desc, name desc'

    name = fields.Char(string='Load Code', readonly=True)
    volume = fields.Float(
        string='Volume',
        help="Load volume must be greater than 0.",
        readonly=True
    )
    load_station_id = fields.Many2one(
        'mrp.workcenter',
        string='Load Station',
        required=True,
        readonly=True,
        help="The station handling this Load, inherited from the Sale Order.\n"
             "Automatically assigned when creating Load from SO.\n"
             "Users may change it manually from available stations."
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        readonly=True,
    )
    bom_id = fields.Many2one(related='sale_order_id.bom_id',string='Mix',store =True)
    mix_note = fields.Text(related='sale_order_id.mix_note',string='Mix Note',store =True,
                           help="Mixing note obtained from the Bill of Materials of the product.")
    delivery_address_id = fields.Many2one(
        related="sale_order_id.partner_shipping_id",
        string='Construction Site Address',
        store=True,
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
        help="Vehicle used to deliver the concrete."
    )
    vehicle_station_id = fields.Many2one(
        'mrp.workcenter',
        string='Vehicle Station',
        help="Station associated with the selected vehicle. "
             "Automatically filled based on vehicle configuration."
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
    )
    company_id = fields.Many2one('res.company', string='Company', required=True,default=lambda self: self.env.company)

    production_ids = fields.One2many('mrp.production','load_id',string='Tickets')
    
    linked_group_workcenter_ids = fields.Many2many(
        'mrp.workcenter',
        compute='_compute_linked_group_workcenters',
        search='_search_linked_group_workcenters',
        store=False,
        string="Linked Group Workcenters")

    @api.depends('load_station_id')
    def _compute_linked_group_workcenters(self):
        for rec in self:
            rec.linked_group_workcenter_ids = rec.load_station_id.linked_group_workcenter_ids

    def _search_linked_group_workcenters(self, operator, value):
        if not value:
            return [('id', '=', 0)]
        if not isinstance(value, (list, tuple)):
            value = [value]
        related_ids = self.env['mrp.workcenter'].browse(value).linked_group_workcenter_ids.ids
        return [('load_station_id', 'in', related_ids)]

    @api.constrains('volume')
    def _check_volume_positive(self):
        for rec in self:
            if not rec.volume or rec.volume <= 0:
                raise ValidationError(_('Volume must be greater than 0.'))
    @api.model
    def create(self, vals):
        today = fields.Date.context_today(self)
        date_str = today.strftime('%Y%m%d')
        seq = self.env['ir.sequence'].next_by_code(
            f'concrete.load.{date_str}'
        )
        if not seq:
            self.env['ir.sequence'].create({
                'name': f'Load {date_str}',
                'code': f'concrete.load.{date_str}',
                'prefix': f'L{date_str}-',
                'padding': 3,
                'number_next': 1,
            })
            seq = self.env['ir.sequence'].next_by_code(
                f'concrete.load.{date_str}'
            )
        vals['name'] = seq
        return super().create(vals)
    
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only Loads in Draft can be deleted."))
        return super().unlink()
    
    def action_set_completed(self):
        self.write({'state':'completed'})
        
    def action_set_draft(self):
        self.write({'state':'draft'})
        
    def action_assign_ticket(self):
        if self.load_station_id != self.vehicle_station_id:
            raise UserError(_("Ticket Assignment Not Possible: Load Station and Vehicle Station are not the same."))
        vals = self._prepare_ticket_vals()
        if not vals.get('bom_id'):
            raise UserError(_("BOM not found."))
        production_id = self.env['mrp.production'].create(vals)
        production_id.with_context(from_assign_ticket=True).action_confirm()
        self.write({'state':'completed'})
        self._create_delivery_order(production_id)

    def _prepare_ticket_vals(self):
        return {
            'load_id':self.id,
            'product_qty':self.volume,
            'product_id':self.product_id.id,
            'bom_id': self._get_bom_assign_ticket().id,
            'company_id':self.company_id.id,
            'mo_type':'concrete',
            'warehouse_id':self.sale_order_id.warehouse_id.id
        }

    def _get_bom_assign_ticket(self):
        return self._get_boms_assign_ticket()[:1]

    def _get_boms_assign_ticket(self):
        MrpBom = self.env['mrp.bom']
        company = self.company_id or self.env.company
        return MrpBom.with_context(active_test=True).search([
            *MrpBom._check_company_domain(company),
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('type', '!=', 'mix')
        ])

    def _create_delivery_order(self,mo):
        group_id = self.env['procurement.group'].search([('sale_id','=',self.sale_order_id.id)],limit=1)
        if not group_id:
            group_id = self.env['procurement.group'].create(self._prepare_procurement_group_vals(self.sale_order_id))
            self.sale_order_id.procurement_group_id = group_id.id
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', '=', self.company_id.id),
            ('warehouse_id', '=', self.sale_order_id.warehouse_id.id),
        ], limit=1)
        if not picking_type:
            raise UserError(_("Operation Type is not define."))
        if not picking_type.default_location_src_id:
            raise UserError(_("Source location is not define."))
        if not picking_type.default_location_dest_id:
            raise UserError(_("Dest location is not define."))
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'company_id': self.company_id.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'ticket_id': mo.id,
            'partner_id': self.delivery_address_id.id,
            'origin': self.name,
        })
        self.env['stock.move'].create({
            'name': self.product_id.display_name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.volume,
            'product_uom': self.product_id.uom_id.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'sale_line_id': self.sale_order_id.order_line[0].id,
            'picking_id': picking.id,
            'company_id': self.company_id.id,
        })
        picking.action_confirm()    
    
    def _prepare_procurement_group_vals(self,sale_id):
        return {
            'name': sale_id.name,
            'move_type': sale_id.picking_policy,
            'sale_id': sale_id.id,
            'partner_id': sale_id.partner_shipping_id.id,
        }
    
    def action_view_ticket(self):
        action = self.env.ref('max_betong_sale.action_concrete_ticket').read()[0]
        action['domain'] = [('id', 'in', self.production_ids.ids)]
        action['view_mode'] = 'tree,form'
        action['context'] = {}
        return action
    
    def _can_cancel_validation(self):
        """Validate if Load can be cancelled
        Returns: list of error messages (empty if valid)
        """
        self.ensure_one()
        errors = []
        
        # Load chỉ được cancel từ Ticket, không từ Load trực tiếp
        # Kiểm tra tất cả tickets liên quan đã cancelled
        tickets = self.production_ids
        non_cancelled_tickets = tickets.filtered(
            lambda t: t.state_concrete != 'cancel'
        )
        
        if non_cancelled_tickets:
            errors.append(
                _("Cannot cancel Load: %s ticket(s) not yet cancelled: %s") % (
                    len(non_cancelled_tickets),
                    ', '.join(non_cancelled_tickets.mapped('name'))
                )
            )
        
        return errors
    
    def action_cancel_from_ticket(self):
        """Cancel Load when all related tickets are cancelled
        This method should only be called from Ticket cancel logic
        """
        for load in self:
            errors = load._can_cancel_validation()
            if errors:
                raise ValidationError('\n'.join(errors))
        self.write({'state': 'cancelled'})
         
    def _check_and_auto_cancel(self):
        """Auto cancel Load if all related tickets are cancelled"""
        self.ensure_one()
        
        # Skip if already cancelled or being cancelled from load level
        if self.state == 'cancelled':
            return
        
        # Don't auto-cancel if we're in a force cancel from load context
        if self.env.context.get('force_cancel_from_load'):
            return
        
        all_tickets = self.production_ids
        if not all_tickets:
            return
        
        # Check tất cả tickets đều cancelled
        all_cancelled = all(
            ticket.state_concrete == 'cancel' 
            for ticket in all_tickets
        )
        
        if all_cancelled:
            self.action_cancel_from_ticket() 
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
    
    