# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ConcreteDashboard(models.AbstractModel):
    _name = 'concrete.dashboard'
    _description = 'Concrete Dashboard'

    @api.model
    def get_dashboard_data(self, params=None):
        if params is None:
            params = {}
        
        station_id = params.get('station_id')
        selected_order_id = params.get('selected_order_id')
        
        return {
            'orders': self._get_orders_data(params.get('orders', {})),
            'loads': self._get_loads_data(params.get('loads', {}), selected_order_id),
            'vehicles': self._get_vehicles_data(params.get('vehicles', {})),
            'tickets': self._get_tickets_data(params.get('tickets', {})),
            'stations': self._get_stations_data(),
        }

    @api.model
    def _get_orders_data(self, params=None):
        if params is None:
            params = {}
        
        page = params.get('page', 1)
        limit = params.get('limit', 10)
        offset = (page - 1) * limit
        
        sort_field = params.get('sort_field', 'name')
        sort_order = params.get('sort_order', 'asc')
        order_str = f'{sort_field} {sort_order}'
        
        field_mapping = {
            'name': 'name',
            'delivery_address': 'partner_shipping_id',
            'product': 'order_line.product_id',
            'mix_note': 'mix_note',
            'station': 'concrete_station_id',
            'volume': 'volume',
            'volume_allocated': 'volume_allocated',
            'volume_unallocated': 'volume_unallocated',
            'state': 'state',
        }
        
        if sort_field in field_mapping:
            order_str = f'{field_mapping[sort_field]} {sort_order}'
        
        search = params.get('search', '')
        
        domain = [
            ('so_type', '=', 'concrete'),
            ('state', 'in', ['planned', 'dispatching'])
        ]
        
        station_id = params.get('station_id')
        if station_id:
            domain.append(('concrete_station_id', '=', station_id))
        
        if search:
            domain.append('|')
            domain.append('|')
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('partner_shipping_id.name', 'ilike', search))
            domain.append(('order_line.product_id.name', 'ilike', search))
            domain.append(('mix_note', 'ilike', search))
        
        total_count = self.env['sale.order'].search_count(domain)
        orders = self.env['sale.order'].search(domain, order=order_str, limit=limit, offset=offset)
        
        data = []
        for o in orders:
            delivered_volume = sum(o.order_line.mapped('qty_delivered'))
            
            data.append({
                'id': o.id,
                'name': o.name,
                'delivery_address': o.partner_shipping_id.name if o.partner_shipping_id else '',
                'delivery_address_id': o.partner_shipping_id.id if o.partner_shipping_id else False,
                'product': o.order_line[0].product_id.name if o.order_line else '',
                'product_id': o.order_line[0].product_id.id if o.order_line else False,
                'mix_note': o.mix_note or '',
                'station': o.concrete_station_id.name if o.concrete_station_id else '',
                'station_id': o.concrete_station_id.id if o.concrete_station_id else False,
                'volume': o.volume,
                'volume_allocated': o.volume_allocated,
                'volume_unallocated': o.volume_unallocated,
                'state': o.state,
                'state_display': dict(o._fields['state'].selection).get(o.state, ''),
                'delivered_volume': delivered_volume,
            })
        
        return {
            'data': data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit if limit else 1,
        }

    @api.model
    def _get_loads_data(self, params=None, selected_order_id=None):
        if params is None:
            params = {}
        
        page = params.get('page', 1)
        limit = params.get('limit', 10)
        offset = (page - 1) * limit
        
        sort_field = params.get('sort_field', 'name')
        sort_order = params.get('sort_order', 'asc')
        order_str = f'{sort_field} {sort_order}'
        
        field_mapping = {
            'name': 'name',
            'delivery_address': 'delivery_address_id',
            'sale_order': 'sale_order_id',
            'product': 'product_id',
            'mix_note': 'mix_note',
            'station': 'load_station_id',
            'volume': 'volume',
        }
        
        if sort_field in field_mapping:
            order_str = f'{field_mapping[sort_field]} {sort_order}'
        
        search = params.get('search', '')
        domain = [('state', '=', 'draft')]
        
        if selected_order_id:
            domain.append(('sale_order_id', '=', selected_order_id))
        
        station_id = params.get('station_id')
        if station_id:
            domain.append(('load_station_id', '=', station_id))
        
        if search:
            domain.append('|')
            domain.append('|')
            domain.append('|')
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('delivery_address_id.name', 'ilike', search))
            domain.append(('sale_order_id.name', 'ilike', search))
            domain.append(('product_id.name', 'ilike', search))
            domain.append(('mix_note', 'ilike', search))
        
        total_count = self.env['concrete.load'].search_count(domain)
        loads = self.env['concrete.load'].search(domain, order=order_str, limit=limit, offset=offset)
        
        data = [{
            'id': l.id,
            'name': l.name,
            'delivery_address': l.delivery_address_id.name if l.delivery_address_id else '',
            'delivery_address_id': l.delivery_address_id.id if l.delivery_address_id else False,
            'sale_order': l.sale_order_id.name if l.sale_order_id else '',
            'sale_order_id': l.sale_order_id.id if l.sale_order_id else False,
            'product': l.product_id.name if l.product_id else '',
            'product_id': l.product_id.id if l.product_id else False,
            'mix_note': l.mix_note or '',
            'station': l.load_station_id.name if l.load_station_id else '',
            'station_id': l.load_station_id.id if l.load_station_id else False,
            'volume': l.volume,
        } for l in loads]
        
        return {
            'data': data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit if limit else 1,
        }

    @api.model
    def _get_vehicles_data(self, params=None):
        if params is None:
            params = {}
        
        page = params.get('page', 1)
        limit = params.get('limit', 10)
        offset = (page - 1) * limit
        search = params.get('search', '')
        
        domain = [('vehicle_type', '=', 'concrete'), ('state_concrete', 'in', ['completed', 'available', 'not_available', 'broken'])]
        
        station_id = params.get('station_id')
        if station_id is not None and station_id != '':
            domain.append(('station_id', '=', station_id))
        
        if search:
            domain.append(('license_plate', 'ilike', search))
        
        all_vehicles = self.env['fleet.vehicle'].search(domain)
        total_count = len(all_vehicles)
        
        # Define priority for vehicle states on the dashboard
        priority_map = {
            'available': 1,      # Available
            'completed': 2,      # Completed
            'not_available': 3,  # Not Available
            'broken': 4,         # Broken
        }
        
        # Sort vehicles: Primary sort by state priority (as defined in priority_map),
        # secondary sort by last update date (write_date) or creation date (create_date)
        sorted_vehicles = all_vehicles.sorted(
            key=lambda v: (priority_map.get(v.state_concrete, 99), v.write_date or v.create_date)
        )
        
        paginated_vehicles = sorted_vehicles[offset:offset + limit]
        
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
        
        data = []
        for v in paginated_vehicles:
            state_concrete = v.state_concrete or 'not_available'
            data.append({
                'id': v.id,
                'name': v.name,
                'license_plate': v.license_plate or v.name or '',
                'station': v.station_id.name if v.station_id else '',
                'station_id': v.station_id.id if v.station_id else False,
                'state_concrete': state_concrete,
                'state_display': state_labels.get(state_concrete, state_concrete),
            })
        
        return {
            'data': data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit if limit else 1,
        }

    @api.model
    def _get_tickets_data(self, params=None):
        if params is None:
            params = {}
        
        page = params.get('page', 1)
        limit = params.get('limit', 10)
        offset = (page - 1) * limit
        
        sort_field = params.get('sort_field', 'name')
        sort_order = params.get('sort_order', 'desc')
        
        field_mapping = {
            'name': 'name',
            'delivery_address': 'delivery_address_id',
            'sale_order': 'sale_order_id',
            'product': 'product_id',
            'mix_note': 'mix_note',
            'station': 'vehicle_station_id',
            'volume': 'product_qty',
            'vehicle': 'vehicle_id',
            'eta': 'eta',
            'state': 'state_concrete',
        }
        
        if sort_field in field_mapping:
            order_str = f'{field_mapping[sort_field]} {sort_order}'
        else:
            order_str = f'{sort_field} {sort_order}'
        
        search = params.get('search', '')
        domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', 'not in', ('draft','dump','remix','swap','cancel')), 
            ('is_invisible_dashboard', '=', False)
        ]
        
        station_id = params.get('station_id')
        if station_id:
            domain.append(('vehicle_station_id', '=', station_id))
        
        if search:
            domain.append('|')
            domain.append('|')
            domain.append('|')
            domain.append('|')
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('delivery_address_id.name', 'ilike', search))
            domain.append(('sale_order_id.name', 'ilike', search))
            domain.append(('product_id.name', 'ilike', search))
            domain.append(('mix_note', 'ilike', search))
            domain.append('|')
            domain.append(('vehicle_id.name', 'ilike', search))
            domain.append(('vehicle_id.license_plate', 'ilike', search))
        
        total_count = self.env['mrp.production'].search_count(domain)
        tickets = self.env['mrp.production'].search(domain, order=order_str, limit=limit, offset=offset)
        
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
            'remix': _('Remix'),
            'swap': _('Swap'),
            'cancel': _('Cancelled'),
        }
        
        data = []
        PROGRESS_STATES = ['assigned', 'loading', 'loaded', 'leave', 'arrived', 'unloading', 'return', 'completed']
        
        for t in tickets:
            state_concrete = t.state_concrete or 'draft'
            
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
                    datetime_field = t.assigned_datetime
                elif state == 'loading':
                    datetime_field = t.loading_datetime
                elif state == 'loaded':
                    datetime_field = t.loaded_datetime
                elif state == 'leave':
                    datetime_field = t.leave_datetime
                elif state == 'arrived':
                    datetime_field = getattr(t, 'arrived_state_tracking_datetime', False) and t.arrived_state_tracking_datetime or False
                elif state == 'unloading':
                    datetime_field = getattr(t, 'unloading_state_tracking_datetime', False) and t.unloading_state_tracking_datetime or False
                elif state == 'return':
                    datetime_field = getattr(t, 'return_state_tracking_datetime', False) and t.return_state_tracking_datetime or False
                elif state == 'completed':
                    datetime_field = getattr(t, 'completed_state_tracking_datetime', False) and t.completed_state_tracking_datetime or False
                
                if datetime_field:
                    if i > highest_passed_index:
                        highest_passed_index = i
                    break
            
            data.append({
                'id': t.id,
                'name': t.name,
                'delivery_address': t.delivery_address_id.name if t.delivery_address_id else '',
                'delivery_address_id': t.delivery_address_id.id if t.delivery_address_id else False,
                'sale_order': t.sale_order_id.name if t.sale_order_id else '',
                'sale_order_id': t.sale_order_id.id if t.sale_order_id else False,
                'product': t.product_id.name if t.product_id else '',
                'product_id': t.product_id.id if t.product_id else False,
                'product_template_id': t.product_id.product_tmpl_id.id if t.product_id and t.product_id.product_tmpl_id else False,
                'mix_note': t.mix_note or '',
                'station': t.load_station_id.name if t.load_station_id else '',
                'station_id': t.load_station_id.id if t.load_station_id else False,
                'volume': t.product_qty,
                'vehicle': t.vehicle_id.license_plate or t.vehicle_id.name if t.vehicle_id else '',
                'vehicle_id': t.vehicle_id.id if t.vehicle_id else False,
                'eta': t.eta.isoformat() if t.eta else '',
                'state': state_concrete,
                'state_display': state_labels.get(state_concrete, state_concrete),
                'assigned_datetime': t.assigned_datetime.isoformat() if t.assigned_datetime else False,
                'loading_datetime': t.loading_datetime.isoformat() if t.loading_datetime else False,
                'loaded_datetime': t.loaded_datetime.isoformat() if t.loaded_datetime else False,
                'leave_datetime': t.leave_datetime.isoformat() if t.leave_datetime else False,
                'arrived_datetime': getattr(t, 'arrived_state_tracking_datetime', False) and t.arrived_state_tracking_datetime.isoformat() or False,
                'unloading_datetime': getattr(t, 'unloading_state_tracking_datetime', False) and t.unloading_state_tracking_datetime.isoformat() or False,
                'return_datetime': getattr(t, 'return_state_tracking_datetime', False) and t.return_state_tracking_datetime.isoformat() or False,
                'completed_datetime': getattr(t, 'completed_state_tracking_datetime', False) and t.completed_state_tracking_datetime.isoformat() or False,
                'highest_passed_state_index': highest_passed_index,  # Highest index state that was passed
            })
        
        return {
            'data': data,
            'total': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit if limit else 1,
        }

    @api.model
    def _get_stations_data(self):
        stations = self.env['mrp.workcenter'].search([])
        return [{
            'id': s.id,
            'name': s.name,
            'code': s.code or '',
        } for s in stations]

    @api.model
    def _check_permission(self, permission):
        """Check if current user has permission"""
        user = self.env.user
        if permission == 'view':
            return user.has_group('max_betong_sale.group_betong_load_user')
        elif permission in ['assign_ticket', 'split_load', 'edit', 'delete']:
            return user.has_group('max_betong_sale.group_betong_load_manager')
        return False

    @api.model
    def get_user_permissions(self):
        """Get user permissions for frontend"""
        return {
            'can_view': self._check_permission('view'),
            'can_assign_ticket': self._check_permission('assign_ticket'),
            'can_split_load': self._check_permission('split_load'),
            'can_edit': self._check_permission('edit'),
            'can_delete': self._check_permission('delete'),
        }

    @api.model
    def assign_ticket(self, load_id, vehicle_id):
        if not self._check_permission('assign_ticket'):
            return {'success': False, 'error': _('You do not have permission to assign ticket')}
        
        load = self.env['concrete.load'].browse(load_id)
        if not load.exists():
            return {'success': False, 'error': _('Load not found')}
        
        vehicle = self.env['fleet.vehicle'].browse(vehicle_id)
        if not vehicle.exists():
            return {'success': False, 'error': _('Vehicle not found')}

        # tạm ẩn
        
        # active_ticket = self.env['mrp.production'].search([
        #     ('vehicle_id', '=', vehicle_id),
        #     ('state', 'not in', ['completed', 'dump', 'remix', 'cancel'])
        # ], limit=1)
        #
        # if active_ticket:
        #     return {'success': False, 'error': _('Cannot Assign Ticket: Vehicle is not Available.')}
        
        load_station_id = load.load_station_id.id if load.load_station_id else False
        vehicle_station_id = vehicle.station_id.id if vehicle.station_id else False
        
        if load_station_id != vehicle_station_id:
            return {'success': False, 'error': _('Cannot Assign Ticket: Load station and Vehicle station do not match.')}
        
        try:
            # Update vehicle info before assigning ticket
            load.write({
                'vehicle_id': vehicle_id,
                'vehicle_station_id': vehicle.station_id.id if vehicle.station_id else False,
            })
            # Assign ticket - this may raise exception
            load.action_assign_ticket()
            return {'success': True}
        except Exception as e:
            # Rollback the transaction on error
            self.env.cr.rollback()
            return {'success': False, 'error': str(e)}

    @api.model
    def split_load(self, order_id):
        if not self._check_permission('split_load'):
            return {'success': False, 'error': _('You do not have permission to split load')}
        
        order = self.env['sale.order'].browse(order_id)
        if not order.exists():
            return {'success': False, 'error': _('Order not found')}
        
        try:
            order.action_split_load()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def delete_load(self, load_id):
        """Delete a single load (kept for backward compatibility)"""
        return self.delete_loads([load_id])
    
    @api.model
    def delete_loads(self, load_ids):
        """Delete multiple loads"""
        if not self._check_permission('delete'):
            return {'success': False, 'error': _('You do not have permission to delete load')}
        
        if not load_ids:
            return {'success': False, 'error': _('No loads selected')}
        
        loads = self.env['concrete.load'].browse(load_ids)
        if not loads.exists():
            return {'success': False, 'error': _('Loads not found')}
        
        try:
            loads.unlink()
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def update_order_station(self, order_id, station_id):
        if not self._check_permission('edit'):
            return {'success': False, 'error': _('You do not have permission to edit')}
        
        order = self.env['sale.order'].browse(order_id)
        if not order.exists():
            return {'success': False, 'error': _('Order not found')}
        
        try:
            order.write({'concrete_station_id': station_id})
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def update_load_station(self, load_id, station_id):
        if not self._check_permission('edit'):
            return {'success': False, 'error': _('You do not have permission to edit')}
        
        load = self.env['concrete.load'].browse(load_id)
        if not load.exists():
            return {'success': False, 'error': _('Load not found')}
        
        try:
            load.write({'load_station_id': station_id})
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def update_vehicle_station(self, vehicle_id, station_id):
        vehicle = self.env['fleet.vehicle'].browse(vehicle_id)
        if not vehicle.exists():
            return {'success': False, 'error': _('Vehicle not found')}
        
        try:
            vehicle.write({'station_id': station_id})
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @api.model
    def update_vehicle_state(self, vehicle_id, state_concrete):
        vehicle = self.env['fleet.vehicle'].browse(vehicle_id)
        if not vehicle.exists():
            return {'success': False, 'error': _('Vehicle not found')}
        
        valid_states = ['available', 'not_available', 'broken']
        if state_concrete not in valid_states:
            return {'success': False, 'error': _('Invalid state')}
        
        current_state = vehicle.state_concrete or 'not_available'
        
        if state_concrete == 'available':
            if current_state not in ['completed', 'not_available', 'broken']:
                return {'success': False, 'error': _('Cannot change to Available from current state')}
        elif state_concrete == 'broken':
            if current_state not in ['completed', 'available', 'not_available']:
                return {'success': False, 'error': _('Cannot change to Broken from current state')}
        elif state_concrete == 'not_available':
            if current_state not in ['completed', 'available', 'broken']:
                return {'success': False, 'error': _('Cannot change to Not Available from current state')}
        
        try:
            if vehicle.state_concrete == 'completed' and state_concrete != 'completed':
                ticket_ids = self.env['mrp.production'].search([('vehicle_id', '=', vehicle_id), ('state_concrete', '=', 'completed')])
                if ticket_ids:
                    ticket_ids[-1].write({'is_invisible_dashboard': True})
            vehicle.write({'state_concrete': state_concrete})
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
