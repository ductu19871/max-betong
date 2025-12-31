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
        help="Load volume must be greater than 0."
    )
    load_station_id = fields.Many2one(
        'mrp.workcenter',
        string='Load Station',
        required=True,
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
        ],
        string='Status',
        default='draft',
    )
    company_id = fields.Many2one('res.company', string='Company', required=True,default=lambda self: self.env.company)
    
    production_ids = fields.One2many('mrp.production','load_id',string='Tickets')
    
    
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
        bom = self.env['mrp.bom'].search([('product_tmpl_id','=',self.product_id.product_tmpl_id.id),
                                          ('type','!=','mix')],limit =1)
        if not bom:
            raise UserError(_("BOM not found."))
        vals={'load_id':self.id,
              'product_qty':self.volume,
              'product_id':self.product_id.id,
              'bom_id':bom.id,
              'mo_type':'concrete',
              'warehouse_id':self.sale_order_id.warehouse_id.id}
        production_id = self.env['mrp.production'].create(vals)
        production_id.action_confirm()
        self.write({'state':'completed'})
    
    def action_view_ticket(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ticket',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.production_ids.ids)],
        } 
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
    
    