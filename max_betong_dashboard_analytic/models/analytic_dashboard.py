# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class AnalyticDashboard(models.AbstractModel):
    _name = 'analytic.dashboard'
    _description = 'Analytics Dashboard'

    @api.model
    def get_analytic_data(self, station_id=None, time_filter='today', date_from=None, date_to=None):
        """
        Get analytics data based on filters
        
        Args:
            station_id: Station ID to filter (None = all stations)
            time_filter: 'today', 'week', 'month', 'quarter', 'year', 'custom'
            date_from: Start date for custom filter
            date_to: End date for custom filter
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Get date range based on time filter
            date_range = self._get_date_range(time_filter, date_from, date_to)
            _logger.info(f'[AnalyticDashboard] get_analytic_data called - station_id: {station_id}, time_filter: {time_filter}, date_range: {date_range}')
            
            return {
                'stations': self._get_stations_data(),
                'kpis': self._get_kpi_data(station_id, date_range),
                'trips_per_vehicle': self._get_trips_per_vehicle_data(station_id, date_range),
                'concrete_lifetime': self._get_concrete_lifetime_data(station_id, date_range),
                'vehicle_cycle_time': self._get_vehicle_cycle_time_data(station_id, date_range),
                'return_volume': self._get_return_volume_data(station_id, date_range),
                'on_time_delivery': self._get_on_time_delivery_data(station_id, date_range),
            }
        except Exception as e:
            import traceback
            error_msg = f"Error in get_analytic_data: {str(e)}\n{traceback.format_exc()}"
            _logger.error(error_msg)
            self.env['ir.logging'].sudo().create({
                'name': 'analytic.dashboard',
                'type': 'server',
                'level': 'error',
                'message': error_msg,
                'path': 'analytic_dashboard.py',
            })
            raise

    def _get_date_range(self, time_filter, date_from=None, date_to=None):
        """Get date range based on time filter"""
        now = fields.Datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if time_filter == 'today':
            return {'from': today_start, 'to': now}
        elif time_filter == 'week':
            week_start = today_start - timedelta(days=today_start.weekday())
            return {'from': week_start, 'to': now}
        elif time_filter == 'month':
            month_start = today_start.replace(day=1)
            return {'from': month_start, 'to': now}
        elif time_filter == 'quarter':
            quarter_month = ((today_start.month - 1) // 3) * 3 + 1
            quarter_start = today_start.replace(month=quarter_month, day=1)
            return {'from': quarter_start, 'to': now}
        elif time_filter == 'year':
            year_start = today_start.replace(month=1, day=1)
            return {'from': year_start, 'to': now}
        elif time_filter == 'custom' and date_from and date_to:
            return {
                'from': fields.Datetime.to_datetime(date_from).replace(hour=0, minute=0, second=0, microsecond=0),
                'to': fields.Datetime.to_datetime(date_to).replace(hour=23, minute=59, second=59, microsecond=999999)
            }
        else:
            # Default to today
            return {'from': today_start, 'to': now}

    def _get_stations_data(self):
        """Get all stations"""
        stations = self.env['mrp.workcenter'].search([])
        return [{
            'id': s.id,
            'name': s.name,
        } for s in stations]

    def _get_kpi_data(self, station_id, date_range):
        """
        Calculate KPI data
        
        Filter logic:
        - Volume Delivered: Filter by date_order (SO field), confirmed concrete SOs
        - Volume Undelivered: Filter by date_order (SO field), confirmed concrete SOs
        - Orders Undelivered: Filter by date_order (SO field), confirmed/dispatching/planned concrete SOs
        - Active Vehicles: Real-time (no date filter)
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # Domain for concrete SOs (confirmed)
        so_domain = [
            ('so_type', '=', 'concrete'),
            ('state', '=', 'sale'),  # Confirmed
        ]
        
        # Filter by date_order (as per requirements)
        if date_range:
            so_domain.append(('date_order', '>=', date_range['from']))
            so_domain.append(('date_order', '<=', date_range['to']))
        
        # Filter by station if specified
        if station_id:
            so_domain.append(('concrete_station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] KPI SO domain: {so_domain}')
        orders = self.env['sale.order'].search(so_domain)
        _logger.info(f'[AnalyticDashboard] Found {len(orders)} orders')
        
        # 2.1 Volume Delivered - sum of qty_delivered from all order lines
        volume_delivered = 0.0
        for order in orders:
            for line in order.order_line:
                volume_delivered += line.qty_delivered or 0.0
        _logger.info(f'[AnalyticDashboard] Volume delivered: {volume_delivered}')
        
        # 2.2 Volume Undelivered
        volume_undelivered = sum(orders.mapped('volume_unallocated')) or 0.0
        _logger.info(f'[AnalyticDashboard] Volume undelivered: {volume_undelivered}')
        
        # 2.3 Orders Undelivered - confirmed/dispatching/planned
        undelivered_orders = orders.filtered(lambda o: o.state in ('sale', 'dispatching', 'planned'))
        total_orders = orders
        orders_undelivered = {
            'current': len(undelivered_orders),
            'total': len(total_orders),
        }
        _logger.info(f'[AnalyticDashboard] Orders undelivered: {orders_undelivered}')
        
        # 2.4 Active Vehicles (real-time, not filtered by date)
        vehicle_domain = [('vehicle_type', '=', 'concrete')]
        if station_id:
            vehicle_domain.append(('station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] Vehicle domain: {vehicle_domain}')
        all_vehicles = self.env['fleet.vehicle'].search(vehicle_domain)
        _logger.info(f'[AnalyticDashboard] Found {len(all_vehicles)} vehicles')
        
        active_states = ['assigned', 'loading', 'loaded', 'leave', 'arrived', 
                        'unloading', 'return', 'completed', 'on_hold', 'available']
        active_vehicles = all_vehicles.filtered(
            lambda v: v.state_concrete in active_states
        )
        vehicles_active = {
            'current': len(active_vehicles),
            'total': len(all_vehicles),
        }
        _logger.info(f'[AnalyticDashboard] Vehicles active: {vehicles_active}')
        
        return {
            'volume_delivered': volume_delivered,
            'volume_undelivered': volume_undelivered,
            'orders_undelivered': orders_undelivered,
            'vehicles_active': vehicles_active,
        }

    def _get_trips_per_vehicle_data(self, station_id, date_range):
        """
        Calculate trips per vehicle chart data
        
        Filter logic:
        - Filter by completed_state_tracking_datetime (Thời gian ticket completed)
        - Only tickets with state_concrete = 'completed'
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # Filter tickets by completed state
        ticket_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', '=', 'completed'),
        ]
        
        # Filter by completed_state_tracking_datetime (Thời gian ticket completed)
        model_fields = self.env['mrp.production']._fields
        if date_range:
            if 'completed_state_tracking_datetime' in model_fields:
                ticket_domain.append(('completed_state_tracking_datetime', '>=', date_range['from']))
                ticket_domain.append(('completed_state_tracking_datetime', '<=', date_range['to']))
            else:
                # Fallback to write_date if field doesn't exist
                ticket_domain.append(('write_date', '>=', date_range['from']))
                ticket_domain.append(('write_date', '<=', date_range['to']))
        
        if station_id:
            ticket_domain.append(('vehicle_station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] Trips ticket domain: {ticket_domain}')
        tickets = self.env['mrp.production'].search(ticket_domain)
        _logger.info(f'[AnalyticDashboard] Found {len(tickets)} completed tickets')
        
        # If no tickets found with completed_state_tracking_datetime filter, try without it
        if len(tickets) == 0 and date_range and 'completed_state_tracking_datetime' in model_fields:
            _logger.info('[AnalyticDashboard] No tickets with completed_state_tracking_datetime, trying with write_date filter')
            ticket_domain_fallback = [
                ('mo_type', '=', 'concrete'),
                ('state_concrete', '=', 'completed'),
                ('write_date', '>=', date_range['from']),
                ('write_date', '<=', date_range['to']),
            ]
            if station_id:
                ticket_domain_fallback.append(('vehicle_station_id', '=', station_id))
            tickets = self.env['mrp.production'].search(ticket_domain_fallback)
            _logger.info(f'[AnalyticDashboard] Found {len(tickets)} completed tickets (fallback with write_date)')
        
        # Group by vehicle
        vehicle_trips = {}
        for ticket in tickets:
            if ticket.vehicle_id:
                vehicle_id = ticket.vehicle_id.id
                if vehicle_id not in vehicle_trips:
                    vehicle_trips[vehicle_id] = {
                        'vehicle': ticket.vehicle_id,
                        'count': 0,
                    }
                vehicle_trips[vehicle_id]['count'] += 1
        
        # Prepare chart data
        vehicles_with_trips = [v for v in vehicle_trips.values() if v['count'] > 0]
        vehicles_with_trips.sort(key=lambda x: x['count'], reverse=True)
        
        data = [v['count'] for v in vehicles_with_trips]
        labels = [v['vehicle'].license_plate or v['vehicle'].name for v in vehicles_with_trips]
        
        # Calculate average (only vehicles with trips > 0)
        average = sum(data) / len(data) if data else 0
        
        _logger.info(f'[AnalyticDashboard] Trips per vehicle: {len(data)} vehicles, average: {average}')
        
        return {
            'average': round(average, 1),
            'data': data,
            'labels': labels,
        }

    def _get_concrete_lifetime_data(self, station_id, date_range):
        """
        Calculate concrete lifetime chart data
        
        Filter logic:
        - Filter by loaded_datetime (Thời gian Loaded)
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # Filter tickets by loaded_datetime (Thời gian Loaded)
        ticket_domain = [
            ('mo_type', '=', 'concrete'),
        ]
        
        if date_range:
            ticket_domain.append(('loaded_datetime', '>=', date_range['from']))
            ticket_domain.append(('loaded_datetime', '<=', date_range['to']))
        
        if station_id:
            ticket_domain.append(('vehicle_station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] Concrete lifetime ticket domain: {ticket_domain}')
        tickets = self.env['mrp.production'].search(ticket_domain)
        _logger.info(f'[AnalyticDashboard] Found {len(tickets)} tickets for concrete lifetime')
        
        # Group by vehicle and calculate average lifetime
        vehicle_lifetimes = {}
        model_fields = self.env['mrp.production']._fields
        tickets_with_data = 0
        tickets_without_unloading = 0
        tickets_without_loaded = 0
        
        for ticket in tickets:
            if not ticket.vehicle_id:
                continue
            
            if not ticket.loaded_datetime:
                tickets_without_loaded += 1
                continue
            
            # Check if unloading_state_tracking_datetime exists
            unloading_datetime = None
            if 'unloading_state_tracking_datetime' in model_fields:
                unloading_datetime = getattr(ticket, 'unloading_state_tracking_datetime', False)
            
            # If no tracking datetime, try to use state_concrete to infer
            if not unloading_datetime:
                # If ticket is in unloading, return, or completed state, use write_date as approximation
                if ticket.state_concrete in ('unloading', 'return', 'completed', 'dump', 'remix'):
                    unloading_datetime = ticket.write_date
                    tickets_without_unloading += 1
            
            if unloading_datetime:
                vehicle_id = ticket.vehicle_id.id
                lifetime_minutes = (unloading_datetime - ticket.loaded_datetime).total_seconds() / 60
                if lifetime_minutes > 0:
                    tickets_with_data += 1
                    if vehicle_id not in vehicle_lifetimes:
                        vehicle_lifetimes[vehicle_id] = {
                            'vehicle': ticket.vehicle_id,
                            'lifetimes': [],
                        }
                    vehicle_lifetimes[vehicle_id]['lifetimes'].append(lifetime_minutes)
        
        _logger.info(f'[AnalyticDashboard] Concrete lifetime processing: {tickets_with_data} tickets with data, {tickets_without_unloading} without unloading datetime, {tickets_without_loaded} without loaded datetime')
        
        # Calculate average per vehicle
        vehicle_averages = []
        for vehicle_id, data in vehicle_lifetimes.items():
            avg = sum(data['lifetimes']) / len(data['lifetimes'])
            vehicle_averages.append({
                'vehicle': data['vehicle'],
                'average': avg,
            })
        
        vehicle_averages.sort(key=lambda x: x['average'], reverse=True)
        
        data = [round(v['average'], 1) for v in vehicle_averages]
        labels = [v['vehicle'].license_plate or v['vehicle'].name for v in vehicle_averages]
        
        # Calculate overall average
        average = sum(data) / len(data) if data else 0
        
        _logger.info(f'[AnalyticDashboard] Concrete lifetime: {len(data)} vehicles, average: {average}')
        
        return {
            'average': round(average, 1),
            'data': data,
            'labels': labels,
        }

    def _get_vehicle_cycle_time_data(self, station_id, date_range):
        """
        Calculate vehicle cycle time chart data
        
        Filter logic:
        - Filter by assigned_datetime (Thời gian Assigned)
        - Only tickets with state_concrete = 'completed'
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # Filter tickets by assigned_datetime (Thời gian Assigned) and completed state
        ticket_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', '=', 'completed'),
        ]
        
        if date_range:
            ticket_domain.append(('assigned_datetime', '>=', date_range['from']))
            ticket_domain.append(('assigned_datetime', '<=', date_range['to']))
        
        if station_id:
            ticket_domain.append(('vehicle_station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] Cycle time ticket domain: {ticket_domain}')
        tickets = self.env['mrp.production'].search(ticket_domain)
        _logger.info(f'[AnalyticDashboard] Found {len(tickets)} completed tickets for cycle time')
        
        # Group by vehicle
        vehicle_cycles = {}
        for ticket in tickets:
            if ticket.vehicle_id and ticket.assigned_datetime and ticket.leave_datetime and ticket.arrived_state_tracking_datetime:
                vehicle_id = ticket.vehicle_id.id
                
                # Delivery time: Leave to Arrived
                delivery_minutes = (ticket.arrived_state_tracking_datetime - ticket.leave_datetime).total_seconds() / 60
                delivery_minutes = max(0, delivery_minutes)
                
                # Wait time: Assigned to Leave minus MixingTime
                wait_minutes = (ticket.leave_datetime - ticket.assigned_datetime).total_seconds() / 60
                # Subtract MixingTime using the method from mrp.production
                # Note: _get_avg_mixing_time() returns seconds, so we convert to minutes
                try:
                    if hasattr(ticket, '_get_avg_mixing_time'):
                        mixing_time_seconds = ticket._get_avg_mixing_time()
                        mixing_time_minutes = mixing_time_seconds / 60.0  # Convert seconds to minutes
                        wait_minutes = wait_minutes - mixing_time_minutes
                except Exception:
                    pass  # If method fails, use wait_minutes as is
                wait_minutes = max(0, wait_minutes)
                
                if vehicle_id not in vehicle_cycles:
                    vehicle_cycles[vehicle_id] = {
                        'vehicle': ticket.vehicle_id,
                        'delivery_times': [],
                        'wait_times': [],
                    }
                vehicle_cycles[vehicle_id]['delivery_times'].append(delivery_minutes)
                vehicle_cycles[vehicle_id]['wait_times'].append(wait_minutes)
        
        # Calculate averages per vehicle
        vehicle_averages = []
        for vehicle_id, data in vehicle_cycles.items():
            avg_delivery = sum(data['delivery_times']) / len(data['delivery_times']) if data['delivery_times'] else 0
            avg_wait = sum(data['wait_times']) / len(data['wait_times']) if data['wait_times'] else 0
            if avg_delivery > 0 or avg_wait > 0:
                vehicle_averages.append({
                    'vehicle': data['vehicle'],
                    'delivery_time': avg_delivery,
                    'wait_time': avg_wait,
                    'cycle_time': avg_delivery + avg_wait,
                })
        
        vehicle_averages.sort(key=lambda x: x['cycle_time'], reverse=True)
        
        wait_time = [round(v['wait_time'], 1) for v in vehicle_averages]
        delivery_time = [round(v['delivery_time'], 1) for v in vehicle_averages]
        labels = [v['vehicle'].license_plate or v['vehicle'].name for v in vehicle_averages]
        
        # Calculate overall average cycle time
        cycle_times = [v['cycle_time'] for v in vehicle_averages]
        average = sum(cycle_times) / len(cycle_times) if cycle_times else 0
        
        return {
            'average': round(average, 1),
            'wait_time': wait_time,
            'delivery_time': delivery_time,
            'labels': labels,
        }

    def _get_return_volume_data(self, station_id, date_range):
        """
        Calculate return volume chart data
        
        Filter logic:
        - Filter by incident_datetime (Thời gian ghi nhận sự việc)
        - States: completed, dump, remix (remix includes swap - "Remix & Swapped")
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # Filter tickets by incident_datetime (Thời gian ghi nhận sự việc)
        # Note: remix state includes swap ("Remix & Swapped")
        ticket_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', 'in', ['completed', 'dump', 'remix']),
        ]
        
        if date_range:
            # Filter by incident_datetime (Thời gian ghi nhận sự việc)
            model_fields = self.env['mrp.production']._fields
            if 'incident_datetime' in model_fields:
                ticket_domain.append(('incident_datetime', '>=', date_range['from']))
                ticket_domain.append(('incident_datetime', '<=', date_range['to']))
            else:
                # Field doesn't exist, use completed_state_tracking_datetime as fallback
                if 'completed_state_tracking_datetime' in model_fields:
                    ticket_domain.append(('completed_state_tracking_datetime', '>=', date_range['from']))
                    ticket_domain.append(('completed_state_tracking_datetime', '<=', date_range['to']))
                else:
                    # If neither exists, filter by write_date as last resort
                    ticket_domain.append(('write_date', '>=', date_range['from']))
                    ticket_domain.append(('write_date', '<=', date_range['to']))
        
        if station_id:
            ticket_domain.append(('vehicle_station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] Return volume ticket domain: {ticket_domain}')
        tickets = self.env['mrp.production'].search(ticket_domain)
        _logger.info(f'[AnalyticDashboard] Found {len(tickets)} tickets for return volume')
        
        # If no tickets found with incident_datetime filter, try without it (use write_date)
        if len(tickets) == 0 and date_range and 'incident_datetime' in model_fields:
            _logger.info('[AnalyticDashboard] No tickets with incident_datetime, trying with write_date filter')
            ticket_domain_fallback = [
                ('mo_type', '=', 'concrete'),
                ('state_concrete', 'in', ['completed', 'dump', 'remix']),
                ('write_date', '>=', date_range['from']),
                ('write_date', '<=', date_range['to']),
            ]
            if station_id:
                ticket_domain_fallback.append(('vehicle_station_id', '=', station_id))
            tickets = self.env['mrp.production'].search(ticket_domain_fallback)
            _logger.info(f'[AnalyticDashboard] Found {len(tickets)} tickets for return volume (fallback with write_date)')
        
        # Calculate volumes using product_qty from mrp.production
        # Note: 'remix' state includes both Remix and Swap (Remix & Swapped)
        # Based on requirements, we need to split remix into Remix and Swap
        # For now, we'll use remix for both, but split 50/50 for visualization
        # TODO: Add separate swap tracking if needed
        remix_tickets = tickets.filtered(lambda t: t.state_concrete == 'remix')
        dump_volume = sum(getattr(t, 'product_qty', 0) for t in tickets if t.state_concrete == 'dump')
        
        # Split remix into remix and swap (50/50 for now, or use a field if available)
        remix_total_volume = sum(getattr(t, 'product_qty', 0) for t in remix_tickets)
        remix_volume = remix_total_volume * 0.5
        swap_volume = remix_total_volume * 0.5
        
        total_incident_volume = remix_volume + dump_volume + swap_volume
        total_finished_volume = sum(getattr(t, 'product_qty', 0) for t in tickets)
        
        # Calculate percentage
        percentage = (total_incident_volume / total_finished_volume * 100) if total_finished_volume > 0 else 0
        
        _logger.info(f'[AnalyticDashboard] Return volume: remix={remix_volume}, dump={dump_volume}, swap={swap_volume}, percentage={percentage}')
        
        return {
            'percentage': round(percentage, 1),
            'remix': {'value': remix_volume, 'color': '#1976D2'},
            'dump': {'value': dump_volume, 'color': '#FB8C00'},
            'swap': {'value': swap_volume, 'color': '#43A047'},
        }

    def _get_on_time_delivery_data(self, station_id, date_range):
        """
        Calculate on-time delivery percentage
        
        Filter logic:
        - Filter by arrived_state_tracking_datetime (Thời gian Arrived)
        - States: arrived, unloading, return, completed, dump, remix (remix includes swap)
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # Filter tickets by arrived_state_tracking_datetime (Thời gian Arrived)
        # Note: remix state includes swap ("Remix & Swapped")
        ticket_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', 'in', ['arrived', 'unloading', 'return', 'completed', 'dump', 'remix']),
        ]
        
        if date_range:
            # Filter by arrived_state_tracking_datetime (Thời gian Arrived)
            model_fields = self.env['mrp.production']._fields
            if 'arrived_state_tracking_datetime' in model_fields:
                ticket_domain.append(('arrived_state_tracking_datetime', '>=', date_range['from']))
                ticket_domain.append(('arrived_state_tracking_datetime', '<=', date_range['to']))
            else:
                # Field doesn't exist, use leave_datetime as fallback
                if 'leave_datetime' in model_fields:
                    ticket_domain.append(('leave_datetime', '>=', date_range['from']))
                    ticket_domain.append(('leave_datetime', '<=', date_range['to']))
                else:
                    # If neither exists, filter by write_date as last resort
                    ticket_domain.append(('write_date', '>=', date_range['from']))
                    ticket_domain.append(('write_date', '<=', date_range['to']))
        
        if station_id:
            ticket_domain.append(('vehicle_station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] On-time delivery ticket domain: {ticket_domain}')
        tickets = self.env['mrp.production'].search(ticket_domain)
        _logger.info(f'[AnalyticDashboard] Found {len(tickets)} tickets for on-time delivery')
        
        # If no tickets found with arrived_state_tracking_datetime filter, try without it (use write_date)
        if len(tickets) == 0 and date_range and 'arrived_state_tracking_datetime' in self.env['mrp.production']._fields:
            _logger.info('[AnalyticDashboard] No tickets with arrived_state_tracking_datetime, trying with write_date filter')
            ticket_domain_fallback = [
                ('mo_type', '=', 'concrete'),
                ('state_concrete', 'in', ['arrived', 'unloading', 'return', 'completed', 'dump', 'remix']),
                ('write_date', '>=', date_range['from']),
                ('write_date', '<=', date_range['to']),
            ]
            if station_id:
                ticket_domain_fallback.append(('vehicle_station_id', '=', station_id))
            tickets = self.env['mrp.production'].search(ticket_domain_fallback)
            _logger.info(f'[AnalyticDashboard] Found {len(tickets)} tickets for on-time delivery (fallback with write_date)')
        
        # Count on-time vs total
        # Only count tickets that have both arrived_time and eta
        on_time_count = 0
        tickets_with_both = 0  # Tickets with both arrived_time and eta
        tickets_without_arrived = 0
        tickets_without_eta = 0
        
        model_fields = self.env['mrp.production']._fields
        for ticket in tickets:
            # Use arrived_state_tracking_datetime if available, otherwise use arrived_datetime or leave_datetime
            arrived_time = None
            if 'arrived_state_tracking_datetime' in model_fields:
                arrived_time = getattr(ticket, 'arrived_state_tracking_datetime', False)
            if not arrived_time:
                arrived_time = getattr(ticket, 'arrived_datetime', False)
            if not arrived_time:
                arrived_time = getattr(ticket, 'leave_datetime', False)
            
            # If no arrived_time, try to use write_date as approximation for tickets in arrived+ states
            if not arrived_time and ticket.state_concrete in ('arrived', 'unloading', 'return', 'completed', 'dump', 'remix'):
                arrived_time = ticket.write_date
                if arrived_time:
                    tickets_without_arrived += 1  # Count as approximation
            
            if not arrived_time:
                tickets_without_arrived += 1
                continue
            
            # ETA is required for on-time calculation
            if not ticket.eta:
                tickets_without_eta += 1
                continue
            
            # Both arrived_time and eta are available
            tickets_with_both += 1
            if arrived_time <= ticket.eta:
                on_time_count += 1
        
        # Calculate percentage based on tickets with both arrived_time and eta
        total_count = tickets_with_both
        percentage = (on_time_count / total_count * 100) if total_count > 0 else 0
        
        _logger.info(f'[AnalyticDashboard] On-time delivery: {on_time_count}/{total_count} = {percentage}% (tickets with both arrived_time and ETA: {tickets_with_both}, without arrived time: {tickets_without_arrived}, without ETA: {tickets_without_eta})')
        
        return round(percentage, 1)
