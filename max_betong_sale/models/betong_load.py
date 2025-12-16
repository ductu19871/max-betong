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
    mix_note = fields.Text(
        string='Mix Note',
        readonly=True,
        help="Mixing note obtained from the Bill of Materials of the product."
    )
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
        related='vehicle_id.station_id',
        string='Vehicle Station',store =True, readonly =False,
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
    
    @api.constrains('volume')
    def _check_volume_positive(self):
        for rec in self:
            if not rec.volume or rec.volume <= 0:
                raise ValidationError(_('Volume must be greater than 0.'))
    
    def _generate_name(self):
        today = fields.Date.context_today(self)
        date_str = today.strftime('%Y%m%d')
        start_dt = datetime.combine(today, time.min)
        end_dt = datetime.combine(today, time.max)
        domain = [('create_date', '>=', start_dt.strftime('%Y-%m-%d 00:00:00')),
                  ('create_date', '<=', end_dt.strftime('%Y-%m-%d 23:59:59'))]
        count_today = self.search_count(domain)
        seq = count_today + 1
        return "L%s-%03d" % (date_str, seq)
    
    @api.model
    def create(self, vals):
        vals['name'] = self._generate_name()
        rec = super().create(vals)
        return rec
    
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only Loads in Draft can be deleted."))
        return super().unlink()
    
    def action_set_completed(self):
        self.write({'state':'completed'})
        
    def action_set_draft(self):
        self.write({'state':'draft'})
        
        
        
        
        
        
        
    
    
    