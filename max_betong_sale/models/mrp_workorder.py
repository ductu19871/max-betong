# -*- coding: utf-8 -*-
from odoo import _, models,fields, api
from odoo.tools import float_round
from datetime import date,timedelta
from odoo.exceptions import ValidationError
class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def write(self, vals):
        res = super().write(vals)
        for wo in self:
            if vals.get('state') == 'progress' or wo.state == 'progress':
                production = wo.production_id
                if production.state == 'progress' and production.mo_type == 'concrete':
                    production.action_loading()
        return res

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible'
    )
    linked_workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string="Linked Workcenter"
    )
    linked_group_workcenter_ids = fields.Many2many(
        'mrp.workcenter',
        compute='_compute_linked_group_workcenters',
        store=False,
        string="Linked Group Workcenters"
    )

    @api.constrains('linked_workcenter_id')
    def _check_reverse_link(self):
        for rec in self:
            other = rec.linked_workcenter_id
            if not other:
                continue
            if other == rec:
                raise ValidationError("A station cannot be linked to itself.")
            if other.linked_workcenter_id and other.linked_workcenter_id != rec:
                raise ValidationError(
                    "The selected station is already linked. Please unlink it first."
                )
            existing = self.env['mrp.workcenter'].search([
                ('linked_workcenter_id', '=', rec.id),
                ('id', '!=', other.id)
            ], limit=1)

            if existing:
                raise ValidationError(
                            "This station has already been linked to another station. Please remove the existing link first.")

    @api.depends('linked_workcenter_id')
    def _compute_linked_group_workcenters(self):
        reverse_map = {}
        if self:
            reverse_records = self.search([
                ('linked_workcenter_id', 'in', self.ids)
            ])
            for wc in self:
                reverse_map[wc.id] = reverse_records.filtered(
                    lambda r: r.linked_workcenter_id.id == wc.id
                )
        for wc in self:
            wc.linked_group_workcenter_ids = (
                wc
                | wc.linked_workcenter_id
                | reverse_map.get(wc.id, self.env['mrp.workcenter'])
            )
    
    def write(self, vals):
        if 'linked_workcenter_id' in vals:
            old_links = {rec.id: rec.linked_workcenter_id for rec in self}

        res = super().write(vals)
        if 'linked_workcenter_id' in vals:
            for rec in self:
                new = rec.linked_workcenter_id
                old = old_links.get(rec.id)
                if not new and old and old.linked_workcenter_id == rec:
                    old.linked_workcenter_id = False
                if new and new.linked_workcenter_id != rec:
                    new.linked_workcenter_id = rec
        return res