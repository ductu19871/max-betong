# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

# Fields that affect search/filter for each model
SEARCH_FILTER_FIELDS = {
    'sale.order': ['name', 'state', 'partner_shipping_id', 'concrete_station_id', 'mix_note', 'so_type'],
    'concrete.load': ['name', 'state', 'delivery_address_id', 'sale_order_id', 'product_id', 'mix_note', 'load_station_id'],
    'fleet.vehicle': ['name', 'license_plate', 'station_id', 'vehicle_type'],
    'mrp.production': ['name', 'state', 'delivery_address_id', 'sale_order_id', 'product_id', 'mix_note', 'vehicle_station_id', 'vehicle_id'],
}


class RealtimeDashboardMixin(models.AbstractModel):
    """Mixin class for realtime dashboard notifications"""
    _name = 'realtime.dashboard.mixin'
    _description = 'Realtime Dashboard Mixin'

    def _get_all_partners(self):
        """Get all active user partners (cached per request)"""
        if not hasattr(self.env, '_dashboard_partners_cache'):
            self.env._dashboard_partners_cache = self.env['res.users'].sudo().search([]).mapped('partner_id')
        return self.env._dashboard_partners_cache

    def _send_notification_to_all_users(self, channel, payload):
        """Send notification to all users via bus"""
        partners = self._get_all_partners()
        bus = self.env['bus.bus']
        for partner in partners:
            bus._sendone(partner, channel, payload)


class SaleOrderRealtimeDashboard(RealtimeDashboardMixin, models.Model):
    _inherit = 'sale.order'

    def _get_dashboard_notify_channel(self):
        """Get channel name for dashboard notifications"""
        return 'dashboard/orders'

    def _prepare_dashboard_data(self):
        """Prepare order data for dashboard realtime update"""
        self.ensure_one()
        delivered_volume = sum(self.order_line.mapped('qty_delivered'))
        return {
            'id': self.id,
            'name': self.name,
            'delivery_address': self.partner_shipping_id.name if self.partner_shipping_id else '',
            'delivery_address_id': self.partner_shipping_id.id if self.partner_shipping_id else False,
            'product': self.order_line[0].product_id.name if self.order_line else '',
            'product_id': self.order_line[0].product_id.id if self.order_line else False,
            'mix_note': self.mix_note or '',
            'station': self.concrete_station_id.name if self.concrete_station_id else '',
            'station_id': self.concrete_station_id.id if self.concrete_station_id else False,
            'volume': self.volume,
            'volume_allocated': self.volume_allocated,
            'volume_unallocated': self.volume_unallocated,
            'state': self.state,
            'state_display': dict(self._fields['state'].selection).get(self.state, ''),
            'delivered_volume': delivered_volume,
        }

    def _send_dashboard_notification(self, action, changed_fields=None):
        """Send notification to dashboard via bus"""
        if changed_fields is None:
            changed_fields = []
        
        # Check if any changed field affects search/filter
        filter_fields = SEARCH_FILTER_FIELDS.get('sale.order', [])
        affects_filter = bool(set(changed_fields) & set(filter_fields))
        
        for record in self:
            if record.so_type != 'concrete' or record.state not in ['planned', 'dispatching']:
                continue
            
            payload = {
                'action': action,
                'model': 'sale.order',
                'record_id': record.id,
                'data': record._prepare_dashboard_data() if action != 'delete' else None,
                'affects_filter': affects_filter,
                'changed_fields': changed_fields,
            }
            
            channel = self._get_dashboard_notify_channel()
            self._send_notification_to_all_users(channel, payload)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._send_dashboard_notification('create', list(vals_list[0].keys()) if vals_list else [])
        return records

    def write(self, vals):
        old_states = {r.id: r.state for r in self}
        old_so_types = {r.id: r.so_type for r in self}
        state_changing = 'state' in vals or 'so_type' in vals
        
        res = super().write(vals)
        
        for record in self:
            old_state = old_states.get(record.id)
            old_so_type = old_so_types.get(record.id)
            
            was_visible = old_so_type == 'concrete' and old_state in ['planned', 'dispatching']
            is_visible = record.so_type == 'concrete' and record.state in ['planned', 'dispatching']
            
            if state_changing:
                if was_visible and not is_visible:
                    payload = {
                        'action': 'delete',
                        'model': 'sale.order',
                        'record_id': record.id,
                        'data': None,
                        'affects_filter': True,
                        'changed_fields': list(vals.keys()),
                    }
                elif not was_visible and is_visible:
                    payload = {
                        'action': 'create',
                        'model': 'sale.order',
                        'record_id': record.id,
                        'data': record._prepare_dashboard_data(),
                        'affects_filter': True,
                        'changed_fields': list(vals.keys()),
                    }
                else:
                    filter_fields = SEARCH_FILTER_FIELDS.get('sale.order', [])
                    affects_filter = bool(set(vals.keys()) & set(filter_fields))
                    payload = {
                        'action': 'update',
                        'model': 'sale.order',
                        'record_id': record.id,
                        'data': record._prepare_dashboard_data(),
                        'affects_filter': affects_filter,
                        'changed_fields': list(vals.keys()),
                    }
                
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
            elif was_visible and is_visible:
                filter_fields = SEARCH_FILTER_FIELDS.get('sale.order', [])
                affects_filter = bool(set(vals.keys()) & set(filter_fields))
                payload = {
                    'action': 'update',
                    'model': 'sale.order',
                    'record_id': record.id,
                    'data': record._prepare_dashboard_data(),
                    'affects_filter': affects_filter,
                    'changed_fields': list(vals.keys()),
                }
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
        
        return res

    def unlink(self):
        ids_to_notify = []
        for record in self:
            if record.so_type == 'concrete' and record.state in ['planned', 'dispatching']:
                ids_to_notify.append(record.id)
        
        res = super().unlink()
        
        if ids_to_notify:
            channel = self._get_dashboard_notify_channel()
            for record_id in ids_to_notify:
                payload = {
                    'action': 'delete',
                    'model': 'sale.order',
                    'record_id': record_id,
                    'data': None,
                    'affects_filter': True,
                    'changed_fields': [],
                }
                self._send_notification_to_all_users(channel, payload)
        return res

    def action_split_load(self):
        res = super().action_split_load()
        for order in self:
            if order.so_type == 'concrete' and order.state in ['planned', 'dispatching']:
                order.invalidate_recordset(['volume_allocated', 'volume_unallocated'])
                payload = {
                    'action': 'update',
                    'model': 'sale.order',
                    'record_id': order.id,
                    'data': order._prepare_dashboard_data(),
                    'affects_filter': False,
                    'changed_fields': ['volume_allocated', 'volume_unallocated'],
                }
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
        return res


class ConcreteLoadRealtimeDashboard(RealtimeDashboardMixin, models.Model):
    _inherit = 'concrete.load'

    def _get_dashboard_notify_channel(self):
        """Get channel name for dashboard notifications"""
        return 'dashboard/loads'

    def _prepare_dashboard_data(self):
        """Prepare load data for dashboard realtime update"""
        self.ensure_one()
        return {
            'id': self.id,
            'name': self.name,
            'delivery_address': self.delivery_address_id.name if self.delivery_address_id else '',
            'delivery_address_id': self.delivery_address_id.id if self.delivery_address_id else False,
            'sale_order': self.sale_order_id.name if self.sale_order_id else '',
            'sale_order_id': self.sale_order_id.id if self.sale_order_id else False,
            'product': self.product_id.name if self.product_id else '',
            'product_id': self.product_id.id if self.product_id else False,
            'mix_note': self.mix_note or '',
            'station': self.load_station_id.name if self.load_station_id else '',
            'station_id': self.load_station_id.id if self.load_station_id else False,
            'volume': self.volume,
        }

    def _send_dashboard_notification(self, action, changed_fields=None):
        """Send notification to dashboard via bus"""
        if changed_fields is None:
            changed_fields = []
        
        filter_fields = SEARCH_FILTER_FIELDS.get('concrete.load', [])
        affects_filter = bool(set(changed_fields) & set(filter_fields))
        
        for record in self:
            if record.state != 'draft':
                continue
            
            payload = {
                'action': action,
                'model': 'concrete.load',
                'record_id': record.id,
                'data': record._prepare_dashboard_data() if action != 'delete' else None,
                'affects_filter': affects_filter,
                'changed_fields': changed_fields,
            }
            
            channel = self._get_dashboard_notify_channel()
            self._send_notification_to_all_users(channel, payload)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._send_dashboard_notification('create', list(vals_list[0].keys()) if vals_list else [])
        return records

    def write(self, vals):
        old_states = {r.id: r.state for r in self}
        
        res = super().write(vals)
        
        for record in self:
            old_state = old_states.get(record.id)
            was_visible = old_state == 'draft'
            is_visible = record.state == 'draft'
            
            if was_visible and not is_visible:
                payload = {
                    'action': 'delete',
                    'model': 'concrete.load',
                    'record_id': record.id,
                    'data': None,
                    'affects_filter': True,
                    'changed_fields': list(vals.keys()),
                }
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
            elif not was_visible and is_visible:
                payload = {
                    'action': 'create',
                    'model': 'concrete.load',
                    'record_id': record.id,
                    'data': record._prepare_dashboard_data(),
                    'affects_filter': True,
                    'changed_fields': list(vals.keys()),
                }
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
            elif was_visible and is_visible:
                filter_fields = SEARCH_FILTER_FIELDS.get('concrete.load', [])
                affects_filter = bool(set(vals.keys()) & set(filter_fields))
                payload = {
                    'action': 'update',
                    'model': 'concrete.load',
                    'record_id': record.id,
                    'data': record._prepare_dashboard_data(),
                    'affects_filter': affects_filter,
                    'changed_fields': list(vals.keys()),
                }
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
        
        return res

    def unlink(self):
        ids_to_notify = []
        for record in self:
            if record.state == 'draft':
                ids_to_notify.append(record.id)
        
        res = super().unlink()
        
        if ids_to_notify:
            channel = self._get_dashboard_notify_channel()
            for record_id in ids_to_notify:
                payload = {
                    'action': 'delete',
                    'model': 'concrete.load',
                    'record_id': record_id,
                    'data': None,
                    'affects_filter': True,
                    'changed_fields': [],
                }
                self._send_notification_to_all_users(channel, payload)
        return res


class FleetVehicleRealtimeDashboard(RealtimeDashboardMixin, models.Model):
    _inherit = 'fleet.vehicle'

    def _get_dashboard_notify_channel(self):
        """Get channel name for dashboard notifications"""
        return 'dashboard/vehicles'

    def _prepare_dashboard_data(self):
        """Prepare vehicle data for dashboard realtime update"""
        self.ensure_one()
        
        state_labels = {
            'not_available': _('Not Available'),
            'available': _('Available'),
            'assigned': _('Assigned'),
            'loading': _('Loading'),
            'loaded': _('Loaded'),
            'leave': _('Leave'),
            'arrived': _('Arrived'),
            'unloading': _('Unloading'),
            'return': _('Return'),
            'completed': _('Completed'),
            'on_hold': _('On Hold'),
            'broken': _('Broken'),
        }
        
        state_concrete = self.state_concrete or 'not_available'
        
        return {
            'id': self.id,
            'name': self.name,
            'license_plate': self.license_plate or '',
            'station': self.station_id.name if self.station_id else '',
            'station_id': self.station_id.id if self.station_id else False,
            'state_concrete': state_concrete,
            'state_display': state_labels.get(state_concrete, state_concrete),
        }

    def _send_dashboard_notification(self, action, changed_fields=None):
        """Send notification to dashboard via bus"""
        if changed_fields is None:
            changed_fields = []
        
        filter_fields = SEARCH_FILTER_FIELDS.get('fleet.vehicle', [])
        affects_filter = bool(set(changed_fields) & set(filter_fields))
        
        for record in self:
            if record.vehicle_type != 'concrete':
                continue
            
            payload = {
                'action': action,
                'model': 'fleet.vehicle',
                'record_id': record.id,
                'data': record._prepare_dashboard_data() if action != 'delete' else None,
                'affects_filter': affects_filter,
                'changed_fields': changed_fields,
            }
            
            channel = self._get_dashboard_notify_channel()
            self._send_notification_to_all_users(channel, payload)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._send_dashboard_notification('create', list(vals_list[0].keys()) if vals_list else [])
        return records

    def write(self, vals):
        old_vehicle_types = {r.id: r.vehicle_type for r in self}
        
        res = super().write(vals)
        
        for record in self:
            old_vehicle_type = old_vehicle_types.get(record.id)
            was_visible = old_vehicle_type == 'concrete'
            is_visible = record.vehicle_type == 'concrete'
            
            if was_visible and not is_visible:
                payload = {
                    'action': 'delete',
                    'model': 'fleet.vehicle',
                    'record_id': record.id,
                    'data': None,
                    'affects_filter': True,
                    'changed_fields': list(vals.keys()),
                }
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
            elif not was_visible and is_visible:
                payload = {
                    'action': 'create',
                    'model': 'fleet.vehicle',
                    'record_id': record.id,
                    'data': record._prepare_dashboard_data(),
                    'affects_filter': True,
                    'changed_fields': list(vals.keys()),
                }
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
            elif was_visible and is_visible:
                filter_fields = SEARCH_FILTER_FIELDS.get('fleet.vehicle', [])
                affects_filter = bool(set(vals.keys()) & set(filter_fields))
                payload = {
                    'action': 'update',
                    'model': 'fleet.vehicle',
                    'record_id': record.id,
                    'data': record._prepare_dashboard_data(),
                    'affects_filter': affects_filter,
                    'changed_fields': list(vals.keys()),
                }
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
        
        return res

    def unlink(self):
        ids_to_notify = []
        for record in self:
            if record.vehicle_type == 'concrete':
                ids_to_notify.append(record.id)
        
        res = super().unlink()
        
        if ids_to_notify:
            channel = self._get_dashboard_notify_channel()
            for record_id in ids_to_notify:
                payload = {
                    'action': 'delete',
                    'model': 'fleet.vehicle',
                    'record_id': record_id,
                    'data': None,
                    'affects_filter': True,
                    'changed_fields': [],
                }
                self._send_notification_to_all_users(channel, payload)
        return res


class MrpProductionRealtimeDashboard(RealtimeDashboardMixin, models.Model):
    _inherit = 'mrp.production'

    def _get_dashboard_notify_channel(self):
        """Get channel name for dashboard notifications"""
        return 'dashboard/tickets'

    def _prepare_dashboard_data(self):
        """Prepare ticket data for dashboard realtime update"""
        self.ensure_one()
        
        state_labels = {
            'draft': _('Draft'),
            'assigned': _('Assigned'),
            'loading': _('Loading'),
            'loaded': _('Loaded'),
            'leave': _('Leave'),
            'arrived': _('Arrived'),
            'unloading': _('Unloading'),
            'return': _('Return'),
            'completed': _('Completed'),
            'on_hold': _('On Hold'),
            'dump': _('Dump'),
            'remix': _('Remix & Swapped'),
            'cancel': _('Cancelled'),
        }
        
        state_concrete = self.state_concrete or 'draft'
        
        PROGRESS_STATES = ['assigned', 'loading', 'loaded', 'leave', 'arrived', 'unloading', 'return', 'completed']
        
        # Find the highest index state that was passed
        # Method 1: Check if current state is in PROGRESS_STATES (before on_hold/cancel)
        highest_passed_index = -1
        if state_concrete in PROGRESS_STATES:
            highest_passed_index = PROGRESS_STATES.index(state_concrete)
        
        # Method 2: Check datetime fields (use existing fields for assigned/loading/loaded/leave, tracking fields for others)
        for i in range(len(PROGRESS_STATES) - 1, -1, -1):
            state = PROGRESS_STATES[i]
            datetime_field = None
            if state == 'assigned':
                datetime_field = self.assigned_datetime
            elif state == 'loading':
                datetime_field = self.loading_datetime
            elif state == 'loaded':
                datetime_field = self.loaded_datetime
            elif state == 'leave':
                datetime_field = self.leave_datetime
            elif state == 'arrived':
                datetime_field = getattr(self, 'arrived_state_tracking_datetime', False) and self.arrived_state_tracking_datetime or False
            elif state == 'unloading':
                datetime_field = getattr(self, 'unloading_state_tracking_datetime', False) and self.unloading_state_tracking_datetime or False
            elif state == 'return':
                datetime_field = getattr(self, 'return_state_tracking_datetime', False) and self.return_state_tracking_datetime or False
            elif state == 'completed':
                datetime_field = getattr(self, 'completed_state_tracking_datetime', False) and self.completed_state_tracking_datetime or False
            
            if datetime_field:
                if i > highest_passed_index:
                    highest_passed_index = i
                break
        
        return {
            'id': self.id,
            'name': self.name,
            'delivery_address': self.delivery_address_id.name if self.delivery_address_id else '',
            'delivery_address_id': self.delivery_address_id.id if self.delivery_address_id else False,
            'sale_order': self.sale_order_id.name if self.sale_order_id else '',
            'sale_order_id': self.sale_order_id.id if self.sale_order_id else False,
            'product': self.product_id.name if self.product_id else '',
            'product_id': self.product_id.id if self.product_id else False,
            'product_template_id': self.product_id.product_tmpl_id.id if self.product_id and self.product_id.product_tmpl_id else False,
            'mix_note': self.mix_note or '',
            'station': self.vehicle_station_id.name if self.vehicle_station_id else '',
            'station_id': self.vehicle_station_id.id if self.vehicle_station_id else False,
            'volume': self.product_qty,
            'vehicle': self.vehicle_id.license_plate or self.vehicle_id.name if self.vehicle_id else '',
            'vehicle_id': self.vehicle_id.id if self.vehicle_id else False,
            'eta': self.eta.isoformat() if self.eta else '',
            'state': state_concrete,
            'state_display': str(state_labels.get(state_concrete, state_concrete)),
            'assigned_datetime': self.assigned_datetime.isoformat() if self.assigned_datetime else False,
            'loading_datetime': self.loading_datetime.isoformat() if self.loading_datetime else False,
            'loaded_datetime': self.loaded_datetime.isoformat() if self.loaded_datetime else False,
            'leave_datetime': self.leave_datetime.isoformat() if self.leave_datetime else False,
            'arrived_datetime': getattr(self, 'arrived_state_tracking_datetime', False) and self.arrived_state_tracking_datetime.isoformat() or False,
            'unloading_datetime': getattr(self, 'unloading_state_tracking_datetime', False) and self.unloading_state_tracking_datetime.isoformat() or False,
            'return_datetime': getattr(self, 'return_state_tracking_datetime', False) and self.return_state_tracking_datetime.isoformat() or False,
            'completed_datetime': getattr(self, 'completed_state_tracking_datetime', False) and self.completed_state_tracking_datetime.isoformat() or False,
            'highest_passed_state_index': highest_passed_index,  # Highest index state that was passed
        }

    def _send_dashboard_notification(self, action, changed_fields=None):
        """Send notification to dashboard via bus"""
        if changed_fields is None:
            changed_fields = []
        
        filter_fields = SEARCH_FILTER_FIELDS.get('mrp.production', [])
        affects_filter = bool(set(changed_fields) & set(filter_fields))
        
        for record in self:
            if record.mo_type != 'concrete' or (record.state_concrete and record.state_concrete == 'draft'):
                continue
            
            payload = {
                'action': action,
                'model': 'mrp.production',
                'record_id': record.id,
                'data': record._prepare_dashboard_data() if action != 'delete' else None,
                'affects_filter': affects_filter,
                'changed_fields': changed_fields,
            }
            
            channel = self._get_dashboard_notify_channel()
            self._send_notification_to_all_users(channel, payload)
        
        if 'state' in changed_fields or 'state_concrete' in changed_fields:
            for record in self:
                if record.vehicle_id:
                    record.vehicle_id._send_dashboard_notification('update', ['status'])

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        concrete_records = records.filtered(lambda r: r.mo_type == 'concrete' and r.state_concrete and r.state_concrete != 'draft')
        if concrete_records:
            concrete_records._send_dashboard_notification('create', list(vals_list[0].keys()) if vals_list else [])
        return records

    def write(self, vals):
        old_mo_types = {r.id: r.mo_type for r in self}
        old_state_concretes = {r.id: r.state_concrete for r in self}
        state_concrete_changing = 'state_concrete' in vals or 'mo_type' in vals
        
        res = super().write(vals)
        
        for record in self:
            old_mo_type = old_mo_types.get(record.id)
            old_state_concrete = old_state_concretes.get(record.id)
            
            was_visible = old_mo_type == 'concrete' and old_state_concrete and old_state_concrete != 'draft'
            is_visible = record.mo_type == 'concrete' and record.state_concrete and record.state_concrete != 'draft'
            
            if state_concrete_changing:
                if was_visible and not is_visible:
                    payload = {
                        'action': 'delete',
                        'model': 'mrp.production',
                        'record_id': record.id,
                        'data': None,
                        'affects_filter': True,
                        'changed_fields': list(vals.keys()),
                    }
                    channel = self._get_dashboard_notify_channel()
                    self._send_notification_to_all_users(channel, payload)
                elif not was_visible and is_visible:
                    payload = {
                        'action': 'create',
                        'model': 'mrp.production',
                        'record_id': record.id,
                        'data': record._prepare_dashboard_data(),
                        'affects_filter': True,
                        'changed_fields': list(vals.keys()),
                    }
                    channel = self._get_dashboard_notify_channel()
                    self._send_notification_to_all_users(channel, payload)
                elif was_visible and is_visible:
                    filter_fields = SEARCH_FILTER_FIELDS.get('mrp.production', [])
                    affects_filter = bool(set(vals.keys()) & set(filter_fields))
                    payload = {
                        'action': 'update',
                        'model': 'mrp.production',
                        'record_id': record.id,
                        'data': record._prepare_dashboard_data(),
                        'affects_filter': affects_filter,
                        'changed_fields': list(vals.keys()),
                    }
                    channel = self._get_dashboard_notify_channel()
                    self._send_notification_to_all_users(channel, payload)
            elif was_visible and is_visible:
                filter_fields = SEARCH_FILTER_FIELDS.get('mrp.production', [])
                affects_filter = bool(set(vals.keys()) & set(filter_fields))
                payload = {
                    'action': 'update',
                    'model': 'mrp.production',
                    'record_id': record.id,
                    'data': record._prepare_dashboard_data(),
                    'affects_filter': affects_filter,
                    'changed_fields': list(vals.keys()),
                }
                channel = self._get_dashboard_notify_channel()
                self._send_notification_to_all_users(channel, payload)
        
        if 'state' in vals or 'state_concrete' in vals:
            for record in self:
                if record.vehicle_id:
                    record.vehicle_id._send_dashboard_notification('update', ['status'])
        
        return res

    def unlink(self):
        ids_to_notify = []
        for record in self:
            if record.mo_type == 'concrete' and record.state_concrete and record.state_concrete != 'draft':
                ids_to_notify.append(record.id)
        
        res = super().unlink()
        
        if ids_to_notify:
            channel = self._get_dashboard_notify_channel()
            for record_id in ids_to_notify:
                payload = {
                    'action': 'delete',
                    'model': 'mrp.production',
                    'record_id': record_id,
                    'data': None,
                    'affects_filter': True,
                    'changed_fields': [],
                }
                self._send_notification_to_all_users(channel, payload)
        return res

