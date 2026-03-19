# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class AnalyticDashboard(models.AbstractModel):
    _name = 'analytic.dashboard'
    _description = 'Analytics Dashboard'

    # Safety guard for clearly broken timestamps.
    # Keep it permissive to avoid empty charts while still skipping obviously bad data.
    # (TASK-8543 does not specify a cap; it only specifies how to compute and to ignore invalid ordering.)
    _MAX_REASONABLE_MINUTES = 30 * 24 * 60

    def _in_range(self, dt, date_range):
        if not dt or not date_range:
            return False
        return date_range['from'] <= dt <= date_range['to']

    def _get_allowed_company_ids(self):
        """Return company ids for dashboard data.

        Use multi-company selection (ticked companies) when available.
        - Prefer `allowed_company_ids` from context (company switcher)
        - Fallback to `env.companies` (active companies recordset)
        - Fallback to current company
        """
        allowed_company_ids = self.env.context.get('allowed_company_ids')
        if allowed_company_ids:
            return allowed_company_ids
        active_company_ids = self.env.companies.ids
        return active_company_ids or [self.env.company.id]

    @api.model
    def get_analytic_data(self, station_id=None, time_filter='today', date_from=None, date_to=None, include_debug=False, allowed_company_ids = []):
        """
        Get analytics data based on filters

        Args:
            station_id: Station ID to filter (None = all stations)
            time_filter: 'today', 'week', 'month', 'quarter', 'year', 'custom'
            date_from: Start date for custom filter (interpreted in user's timezone)
            date_to: End date for custom filter (interpreted in user's timezone)
            include_debug: Include debug info (domains, record IDs) for debugging
            
        Timezone Handling:
            - User timezone is automatically retrieved from session context (self.env.context.get('tz'))
            - All date filters are calculated relative to user's local time
            - Database queries use UTC (Odoo standard)
            - This ensures "today" means today in user's timezone, not server timezone
        """
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # Get date range based on time filter
            date_range = self._get_date_range(time_filter, date_from, date_to)
            
            # Log chi tiết về date range filter
            _logger.info(
                f'[AnalyticDashboard] ═══════════════════════════════════════════════════\n'
                f'[AnalyticDashboard] FILTER DATE RANGE:\n'
                f'  Time Filter: {time_filter}\n'
                f'  Custom From: {date_from}\n'
                f'  Custom To: {date_to}\n'
                f'  Station ID: {station_id}\n'
                f'  ─────────────────────────────────────\n'
                f'  UTC Range (for DB query):\n'
                f'    From: {date_range["from"] if date_range else "None"}\n'
                f'    To:   {date_range["to"] if date_range else "None"}\n'
                f'[AnalyticDashboard] ═══════════════════════════════════════════════════'
            )

            if not self.env.context.get('allowed_company_ids') and allowed_company_ids:
                self = self.with_context(allowed_company_ids=allowed_company_ids)
            result = {
                'stations': self._get_stations_data(),
                'kpis': self._get_kpi_data(station_id, date_range),
                'trips_per_vehicle': self._get_trips_per_vehicle_data(station_id, date_range),
                'concrete_lifetime': self._get_concrete_lifetime_data(station_id, date_range),
                'vehicle_cycle_time': self._get_vehicle_cycle_time_data(station_id, date_range),
                'return_volume': self._get_return_volume_data(station_id, date_range),
                'on_time_delivery': self._get_on_time_delivery_data(station_id, date_range),
            }

            # Add debug info if requested
            if include_debug:
                result['debug'] = self._get_debug_data(station_id, date_range)

            return result
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
        """Get date range based on time filter with Timezone support
        
        TIMEZONE SYNCHRONIZATION:
        - User's timezone is retrieved from session context (web request) or user preferences
        - All date ranges are calculated in user's timezone
        - Results are converted to naive UTC for database queries
        - This ensures dashboard displays data relative to user's local time
        """
        import pytz
        import re
        from dateutil import parser as dateutil_parser
        
        # Get UTC now and User's Timezone (prefer context tz from session)
        user_tz_str = self.env.context.get('tz') or self.env.user.tz or 'UTC'
        user_tz = pytz.timezone(user_tz_str)
        course_utc = fields.Datetime.now()
        
        # Convert UTC now to User's Timezone
        # fields.Datetime.now() returns naive UTC datetime, so we localize it to UTC first
        context_now = pytz.utc.localize(course_utc).astimezone(user_tz)
        
        # Calculate Start of Day in User's Timezone (not UTC!)
        today_start_user = context_now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        start_dt = None
        end_dt = context_now # Default end is now
        
        if time_filter == 'today':
            start_dt = today_start_user
            
        elif time_filter == 'week':
            # Monday is 0, Sunday is 6
            start_dt = today_start_user - timedelta(days=today_start_user.weekday())
            
        elif time_filter == 'month':
            start_dt = today_start_user.replace(day=1)
            
        elif time_filter == 'quarter':
            quarter_month = ((today_start_user.month - 1) // 3) * 3 + 1
            start_dt = today_start_user.replace(month=quarter_month, day=1)
            
        elif time_filter == 'year':
            start_dt = today_start_user.replace(month=1, day=1)
            
        elif time_filter == 'custom' and date_from and date_to:
            # For custom range, we trust the inputs (assuming they are already handled or raw matches)
            # Though usually frontend sends local time. We might need to assume these are in User TZ?
            # Let's check how default 'custom' passed data. 
            # If date_from/date_to are strings "YYYY-MM-DDTHH:MM", they are practically naive.
            # We treat them as User TZ time and convert to UTC.
            
            try:
                original_date_from = date_from
                original_date_to = date_to

                # Frontend uses <input type="datetime-local"> which typically sends `YYYY-MM-DDTHH:MM`.
                # Normalize to an Odoo-friendly datetime string before parsing.
                if isinstance(date_from, str):
                    date_from = date_from.replace('T', ' ')
                    if len(date_from) == 16:
                        date_from = f"{date_from}:00"
                if isinstance(date_to, str):
                    date_to = date_to.replace('T', ' ')
                    if len(date_to) == 16:
                        date_to = f"{date_to}:00"

                def _parse_maybe_tzaware(value):
                    if not isinstance(value, str):
                        return value
                    # ISO with timezone (e.g. ...Z or ...+07:00)
                    if re.search(r'(Z|[+-]\d{2}:?\d{2})$', value.strip()):
                        return dateutil_parser.isoparse(value)
                    return fields.Datetime.to_datetime(value)

                dt_from = _parse_maybe_tzaware(date_from)
                dt_to = _parse_maybe_tzaware(date_to)
                
                if dt_from and dt_to:
                    # If tz-aware, use it directly. Otherwise assume input is in User TZ.
                    if getattr(dt_from, 'tzinfo', None) is not None:
                        start_dt = dt_from.astimezone(user_tz)
                    else:
                        start_dt = user_tz.localize(dt_from)

                    if getattr(dt_to, 'tzinfo', None) is not None:
                        end_dt = dt_to.astimezone(user_tz)
                    else:
                        end_dt = user_tz.localize(dt_to)

                    # HTML datetime-local is typically minute precision.
                    # Make `to` inclusive for that minute so records at HH:MM:SS aren't dropped.
                    if getattr(dt_to, 'second', 0) == 0 and getattr(dt_to, 'microsecond', 0) == 0:
                        end_dt = end_dt + timedelta(seconds=59, microseconds=999999)

                    # Heuristic fallback: if the tz-converted range yields zero records,
                    # try interpreting inputs as UTC-naive (common if stored timestamps are UTC-naive already).
                    try:
                        probe_from_utc = start_dt.astimezone(pytz.utc).replace(tzinfo=None)
                        probe_to_utc = end_dt.astimezone(pytz.utc).replace(tzinfo=None)
                        probe_domain = [
                            ('company_id', 'in', self._get_allowed_company_ids()),
                            ('write_date', '>=', probe_from_utc),
                            ('write_date', '<=', probe_to_utc),
                        ]
                        probe_count = self.env['mrp.production'].sudo().search_count(probe_domain)

                        if probe_count == 0 and isinstance(original_date_from, str) and isinstance(original_date_to, str):
                            # Parse again as naive UTC (no user tz localization)
                            dt_from_utc_naive = fields.Datetime.to_datetime(original_date_from.replace('T', ' ') + (':00' if len(original_date_from.replace('T', ' ')) == 16 else ''))
                            dt_to_utc_naive = fields.Datetime.to_datetime(original_date_to.replace('T', ' ') + (':00' if len(original_date_to.replace('T', ' ')) == 16 else ''))
                            if dt_from_utc_naive and dt_to_utc_naive:
                                start_dt = pytz.utc.localize(dt_from_utc_naive).astimezone(user_tz)
                                end_dt = pytz.utc.localize(dt_to_utc_naive).astimezone(user_tz)
                                if dt_to_utc_naive.second == 0 and dt_to_utc_naive.microsecond == 0:
                                    end_dt = end_dt + timedelta(seconds=59, microseconds=999999)
                    except Exception:
                        pass
                else:
                    start_dt = today_start_user
            except:
                start_dt = today_start_user
        else:
            start_dt = today_start_user

        # Final check if start_dt was set
        if not start_dt:
             start_dt = today_start_user

        # Convert back to naive UTC for Odoo domain search
        # astimezone(pytz.utc) converts to UTC
        # replace(tzinfo=None) makes it naive (Odoo stores datetimes as naive UTC)
        date_from_utc = start_dt.astimezone(pytz.utc).replace(tzinfo=None)
        date_to_utc = end_dt.astimezone(pytz.utc).replace(tzinfo=None)
        
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(
            f"[Timezone Sync] Dashboard Date Range ({time_filter}):\n"
            f"  User TZ: {user_tz_str}\n"
            f"  User Local: {start_dt.strftime('%Y-%m-%d %H:%M:%S %Z')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
            f"  DB Query (UTC): {date_from_utc} to {date_to_utc}"
        )
        
        return {'from': date_from_utc, 'to': date_to_utc}

    def _get_stations_data(self):
        """Get all stations filtered by user's allowed companies"""
        station_domain = [('company_id', 'in', self._get_allowed_company_ids())]
        stations = self.env['mrp.workcenter'].search(station_domain, order='name')
        return [{
            'id': s.id,
            'name': s.name,
        } for s in stations]

    def _get_kpi_data(self, station_id, date_range):
        """
        Calculate KPI data

        Notes:
        - As requested: delivered/remaining are taken from `sale.order.line`.
        - `volume_delivered` uses `sale.order.line.qty_delivered`.
        - `volume_undelivered` = ordered quantity - delivered quantity.

        Filter logic:
        - Filter SOs by `sale.order.date_order` (per TASK-8543 table).
        - `vehicles_active`: realtime (no date filter)
        """
        import logging
        _logger = logging.getLogger(__name__)

        # --- All confirmed concrete SOs (spec 4.1/4.2: "SO Bê tông đã xác nhận") ---
        so_domain = [
            ('so_type', '=', 'concrete'),
            ('state', 'in', ('sale', 'planned', 'dispatching', 'done')),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        if date_range:
            so_domain.append(('date_order', '>=', date_range['from']))
            so_domain.append(('date_order', '<=', date_range['to']))
        if station_id:
            so_domain.append(('concrete_station_id', '=', station_id))

        _logger.debug(f'[AnalyticDashboard] KPI SO domain: {so_domain}')
        all_orders = self.env['sale.order'].search(so_domain)

        volume_delivered = 0.0
        volume_undelivered = 0.0
        for order in all_orders:
            concrete_lines = order.order_line.filtered(
                lambda l: (not l.display_type)
                and l.product_id
                and getattr(l.product_id, 'is_concrete_product', False)
            )

            ordered_qty = sum(concrete_lines.mapped('product_uom_qty')) if concrete_lines else (order.volume or 0.0)
            delivered_qty = sum(concrete_lines.mapped('qty_delivered')) if concrete_lines else 0.0
            remaining_qty = ordered_qty - delivered_qty

            volume_delivered += delivered_qty
            volume_undelivered += remaining_qty

        volume_delivered = round(volume_delivered, 1)
        volume_undelivered = round(volume_undelivered, 1)

        # --- Undelivered orders KPI ---
        # As requested: "đơn chưa giao" = tổng đơn - đơn đã hoàn tất.
        done_count = len(all_orders.filtered(lambda o: o.state == 'done'))
        undelivered_order_count = max(len(all_orders) - done_count, 0)

        orders_undelivered = {
            'current': undelivered_order_count,
            'total': len(all_orders),
        }

        vehicle_domain = [
            ('vehicle_type', '=', 'concrete'),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        if station_id:
            vehicle_domain.append(('station_id', '=', station_id))

        _logger.debug(f'[AnalyticDashboard] Vehicle domain: {vehicle_domain}')
        all_vehicles = self.env['fleet.vehicle'].search(vehicle_domain)
        _logger.debug(f'[AnalyticDashboard] Found {len(all_vehicles)} vehicles')

        active_states = [
            'assigned', 'loading', 'loaded', 'leave', 'arrived',
            'unloading', 'return', 'completed', 'on_hold', 'available'
        ]
        active_vehicles = all_vehicles.filtered(lambda v: v.state_concrete in active_states)
        vehicles_active = {
            'current': len(active_vehicles),
            'total': len(all_vehicles),
        }

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
        - Filter ONLY by completed_state_tracking_datetime (NO fallback)
        - Only tickets with state_concrete = 'completed'
        - Domain: [("mo_type", "=", "concrete"), ("state_concrete", "=", "completed"), ("completed_state_tracking_datetime", ">=", ...), ("completed_state_tracking_datetime", "<=", ...)]
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # CHỈ filter theo completed_state_tracking_datetime
        ticket_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', '=', 'completed'),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        
        if date_range:
            ticket_domain.append(('completed_state_tracking_datetime', '>=', date_range['from']))
            ticket_domain.append(('completed_state_tracking_datetime', '<=', date_range['to']))
        
        if station_id:
            ticket_domain.append(('vehicle_station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] Trips Per Vehicle - Domain: {ticket_domain}')
        tickets = self.env['mrp.production'].search(ticket_domain)
        _logger.info(f'[AnalyticDashboard] Trips Per Vehicle - Found {len(tickets)} tickets')
        
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
        labels = [v['vehicle'].ref or v['vehicle'].name for v in vehicles_with_trips]
        
        # Calculate average (only vehicles with trips > 0)
        average = sum(data) / len(data) if data else 0
        
        # Detailed logging
        top_5_vehicles = vehicles_with_trips[:5]
        top_5_details = [
            f"{v['vehicle'].ref or v['vehicle'].name}: {v['count']} chuyến"
            for v in top_5_vehicles
        ]
        
        _logger.info(
            f'[AnalyticDashboard] Trips Per Vehicle Chart:\n'
            f'  Total tickets: {len(tickets)}\n'
            f'  Vehicles with trips: {len(vehicles_with_trips)}\n'
            f'  Average trips/vehicle: {average:.1f} chuyến\n'
            f'  Trips range: {min(data) if data else 0} - {max(data) if data else 0} chuyến\n'
            f'  Top 5 vehicles:\n    ' + '\n    '.join(top_5_details if top_5_details else ['N/A'])
        )
        
        return {
            'average': round(average, 1),
            'data': data,
            'labels': labels,
        }

    def _get_concrete_lifetime_data(self, station_id, date_range):
        """
        Calculate concrete lifetime chart data
        
        Yêu cầu:
        - Thời gian sống bê tông tính từ lúc ticket: Loaded đến Unloading
        - Công thức: Unloading_datetime - Loaded_datetime
        - Nếu giá trị âm thì trả về 0
        - Trung bình: CHỈ tính giá trị > 0
        
        Filter logic:
        - Filter ONLY by loaded_datetime (NO fallback)
        - Domain: [("mo_type", "=", "concrete"), ("loaded_datetime", ">=", ...), ("loaded_datetime", "<=", ...)]
        """
        import logging
        _logger = logging.getLogger(__name__)

        # CHỈ filter theo loaded_datetime (Thời gian Loaded)
        ticket_domain = [
            ('mo_type', '=', 'concrete'),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        
        if date_range:
            ticket_domain.append(('loaded_datetime', '>=', date_range['from']))
            ticket_domain.append(('loaded_datetime', '<=', date_range['to']))
        
        if station_id:
            ticket_domain.append(('vehicle_station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] Concrete Lifetime - Domain: {ticket_domain}')
        tickets = self.env['mrp.production'].search(ticket_domain)
        _logger.info(f'[AnalyticDashboard] Concrete Lifetime - Found {len(tickets)} tickets')
        
        # Group by vehicle and calculate average lifetime
        # Yêu cầu: Thời gian sống bê tông = Unloading - Loaded
        # Chỉ tính trung bình những giá trị > 0
        vehicle_lifetimes = {}
        tickets_with_loaded = 0
        tickets_without_loaded = 0
        tickets_outlier = 0
        tickets_invalid_order = 0
        
        for ticket in tickets:
            if not ticket.vehicle_id:
                continue
            
            # Start time: Loaded datetime (khi bê tông bắt đầu "sống")
            start_dt = ticket.loaded_datetime
            if not start_dt:
                tickets_without_loaded += 1
                continue

            tickets_with_loaded += 1

            # End time: Unloading datetime (khi bê tông kết thúc "sống")
            end_dt = ticket.unloading_state_tracking_datetime

            lifetime_minutes = 0.0
            if end_dt:
                if end_dt < start_dt:
                    # Nếu thời gian không hợp lệ (unloading < loaded) → 0
                    tickets_invalid_order += 1
                    lifetime_minutes = 0.0
                else:
                    lifetime_minutes = (end_dt - start_dt).total_seconds() / 60

            # Skip outliers (thời gian quá lớn, không hợp lý)
            if lifetime_minutes > self._MAX_REASONABLE_MINUTES:
                tickets_outlier += 1
                continue

            vehicle_id = ticket.vehicle_id.id
            if vehicle_id not in vehicle_lifetimes:
                vehicle_lifetimes[vehicle_id] = {
                    'vehicle': ticket.vehicle_id,
                    'lifetimes': [],
                }
            # Nếu âm → 0 (max(0.0, ...))
            vehicle_lifetimes[vehicle_id]['lifetimes'].append(max(0.0, lifetime_minutes))
        
        _logger.debug(
            f'[AnalyticDashboard] Concrete lifetime processing: {tickets_with_loaded} tickets with loaded, '
            f'{tickets_without_loaded} without loaded datetime, '
            f'{tickets_invalid_order} invalid ordering, '
            f'{tickets_outlier} outlier skipped (>{self._MAX_REASONABLE_MINUTES} min)'
        )
        
        # Calculate TB mỗi xe (per-vehicle average)
        # Bar = TB mỗi xe (average). TB overall = average of "TB mỗi xe" per file mrp.csv
        vehicle_totals = []
        for vehicle_id, data in vehicle_lifetimes.items():
            lifetimes_pos = [m for m in data['lifetimes'] if m and m > 0]
            if not lifetimes_pos:
                continue
            total = sum(lifetimes_pos)
            count = len(lifetimes_pos)
            avg_per_vehicle = total / count  # TB mỗi xe (bar value)
            vehicle_totals.append({
                'vehicle': data['vehicle'],
                'total': total,
                'count': count,
                'avg_per_vehicle': avg_per_vehicle,
            })
        
        vehicle_totals.sort(key=lambda x: x['avg_per_vehicle'], reverse=True)
        
        data = [round(v['avg_per_vehicle'], 1) for v in vehicle_totals]  # Bar = TB mỗi xe
        labels = [v['vehicle'].ref or v['vehicle'].name for v in vehicle_totals]
        
        # Overall TB = average of "TB mỗi xe" (per mrp.csv row 50: TB = 3.725)
        avg_per_vehicles = [v['avg_per_vehicle'] for v in vehicle_totals if v.get('avg_per_vehicle') and v['avg_per_vehicle'] > 0]
        average = (sum(avg_per_vehicles) / len(avg_per_vehicles)) if avg_per_vehicles else 0
        
        # Top 5 vehicles with longest TB mỗi xe
        top_5_vehicles = vehicle_totals[:5]
        top_5_details = [
            f"{v['vehicle'].ref or v['vehicle'].name}: {v['avg_per_vehicle']:.1f} phút (TB mỗi xe)"
            for v in top_5_vehicles
        ]
        
        _logger.info(
            f'[AnalyticDashboard] Concrete Lifetime Chart:\n'
            f'  Total tickets: {len(tickets)}\n'
            f'  Tickets with loaded datetime: {tickets_with_loaded}\n'
            f'  Vehicles with data: {len(vehicle_totals)}\n'
            f'  TB (avg of TB mỗi xe, per mrp.csv): {average:.1f} phút\n'
            f'  TB mỗi xe range: {min(data) if data else 0:.1f} - {max(data) if data else 0:.1f} phút\n'
            f'  Top 5 longest TB mỗi xe:\n    ' + '\n    '.join(top_5_details if top_5_details else ['N/A']) + '\n'
            f'  Skipped: without_loaded={tickets_without_loaded}, invalid_order={tickets_invalid_order}, outlier={tickets_outlier}'
        )
        
        return {
            'average': round(average, 1),
            'data': data,
            'labels': labels,
        }

    def _get_vehicle_cycle_time_data(self, station_id, date_range):
        """
        Calculate vehicle cycle time chart data
        
        Filter logic:
        - Filter ONLY by assigned_datetime (NO fallback)
        - Only tickets with state_concrete = 'completed'
        - Domain: [("mo_type", "=", "concrete"), ("assigned_datetime", ">=", ...), ("assigned_datetime", "<=", ...), ("state_concrete", "=", "completed")]

        Excel formula:
        - Wait time (TG chờ tại trạm) = leave_datetime - assigned_datetime
        - Delivery time (TG giao hàng) = completed_state_tracking_datetime - leave_datetime
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # CHỈ filter theo assigned_datetime (Thời gian Assigned)
        ticket_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', '=', 'completed'),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        
        if date_range:
            ticket_domain.append(('assigned_datetime', '>=', date_range['from']))
            ticket_domain.append(('assigned_datetime', '<=', date_range['to']))
        
        if station_id:
            ticket_domain.append(('vehicle_station_id', '=', station_id))
        
        _logger.info(f'[AnalyticDashboard] Vehicle Cycle Time - Domain: {ticket_domain}')
        tickets = self.env['mrp.production'].search(ticket_domain)
        _logger.info(f'[AnalyticDashboard] Vehicle Cycle Time - Found {len(tickets)} tickets')
        
        # Group by vehicle
        vehicle_cycles = {}
        tickets_outlier = 0
        tickets_missing_end = 0
        tickets_inconsistent = 0

        for ticket in tickets:
            if not (ticket.vehicle_id and ticket.assigned_datetime and ticket.leave_datetime):
                continue

            # Excel uses Completed tracking datetime only (no fallback)
            end_dt = ticket.completed_state_tracking_datetime
            if not end_dt:
                tickets_missing_end += 1
                continue

            # Guard against inconsistent timestamps
            if ticket.leave_datetime < ticket.assigned_datetime or end_dt < ticket.leave_datetime:
                tickets_inconsistent += 1
                continue

            vehicle_id = ticket.vehicle_id.id

            # Delivery time: Leave to End (prefer Completed tracking)
            delivery_minutes = (end_dt - ticket.leave_datetime).total_seconds() / 60
            delivery_minutes = max(0, delivery_minutes)

            # Plant/wait time: Assigned to Leave
            wait_minutes = (ticket.leave_datetime - ticket.assigned_datetime).total_seconds() / 60
            wait_minutes = max(0, wait_minutes)

            # Keep tickets with a valid delivery duration. Wait time may be 0 (Excel can show 0).
            if delivery_minutes <= 0:
                continue

            if delivery_minutes > self._MAX_REASONABLE_MINUTES or wait_minutes > self._MAX_REASONABLE_MINUTES:
                tickets_outlier += 1
                continue

            if vehicle_id not in vehicle_cycles:
                vehicle_cycles[vehicle_id] = {
                    'vehicle': ticket.vehicle_id,
                    'delivery_times': [],
                    'wait_times': [],
                }
            vehicle_cycles[vehicle_id]['delivery_times'].append(delivery_minutes)
            vehicle_cycles[vehicle_id]['wait_times'].append(wait_minutes)

        if tickets_missing_end or tickets_inconsistent or tickets_outlier:
            _logger.debug(
                f'[AnalyticDashboard] Cycle time: missing_end={tickets_missing_end}, '
                f'inconsistent={tickets_inconsistent}, '
                f'outlier_skipped={tickets_outlier} (>{self._MAX_REASONABLE_MINUTES} min)'
            )
        
        # Calculate TB mỗi xe (per-vehicle average)
        # Bar = TB mỗi xe (delivery avg, wait avg). TB overall = average of per-vehicle avg cycle per mrp (1).csv
        vehicle_totals = []
        for vehicle_id, data in vehicle_cycles.items():
            delivery_pos = [m for m in data['delivery_times'] if m and m > 0]
            total_delivery = sum(delivery_pos) if delivery_pos else 0
            wait_pos = [m for m in data['wait_times'] if m and m > 0]
            total_wait = sum(wait_pos) if wait_pos else 0
            
            if total_delivery > 0 and total_wait > 0:
                count = len(delivery_pos)  # same as len(wait_pos)
                avg_delivery_per_vehicle = total_delivery / count  # TB delivery mỗi xe (bar value)
                avg_wait_per_vehicle = total_wait / count  # TB wait mỗi xe (bar value)
                cycle_total = total_delivery + total_wait
                avg_cycle_per_vehicle = cycle_total / count  # TB chu kỳ mỗi xe
                vehicle_totals.append({
                    'vehicle': data['vehicle'],
                    'delivery_time': avg_delivery_per_vehicle,  # Bar = TB mỗi xe
                    'wait_time': avg_wait_per_vehicle,  # Bar = TB mỗi xe
                    'cycle_time': cycle_total,
                    'count': count,
                    'avg_cycle_per_vehicle': avg_cycle_per_vehicle,
                })
        
        vehicle_totals.sort(key=lambda x: x['avg_cycle_per_vehicle'], reverse=True)
        
        wait_time = [round(v['wait_time'], 1) for v in vehicle_totals]  # TB mỗi xe
        delivery_time = [round(v['delivery_time'], 1) for v in vehicle_totals]  # TB mỗi xe
        labels = [v['vehicle'].ref or v['vehicle'].name for v in vehicle_totals]
        
        # Overall TB = average of "TB mỗi xe" (per-vehicle average cycle), per mrp (1).csv row 21: TB = 401.06
        avg_cycles = [v['avg_cycle_per_vehicle'] for v in vehicle_totals if v.get('avg_cycle_per_vehicle') and v['avg_cycle_per_vehicle'] > 0]
        average = (sum(avg_cycles) / len(avg_cycles)) if avg_cycles else 0
        
        # Top 5 vehicles with longest TB chu kỳ mỗi xe
        top_5_vehicles = vehicle_totals[:5]
        top_5_details = [
            f"{v['vehicle'].ref or v['vehicle'].name}: {v['avg_cycle_per_vehicle']:.1f} phút (TB - Delivery: {v['delivery_time']:.1f}, Wait: {v['wait_time']:.1f})"
            for v in top_5_vehicles
        ]
        
        _logger.info(
            f'[AnalyticDashboard] Vehicle Cycle Time Chart:\n'
            f'  Total tickets: {len(tickets)}\n'
            f'  Vehicles with data: {len(vehicle_totals)}\n'
            f'  TB (avg of TB chu kỳ mỗi xe, per mrp (1).csv): {average:.1f} phút\n'
            f'  TB delivery mỗi xe range: {min(delivery_time) if delivery_time else 0:.1f} - {max(delivery_time) if delivery_time else 0:.1f} phút\n'
            f'  TB wait mỗi xe range: {min(wait_time) if wait_time else 0:.1f} - {max(wait_time) if wait_time else 0:.1f} phút\n'
            f'  Top 5 longest TB chu kỳ mỗi xe:\n    ' + '\n    '.join(top_5_details if top_5_details else ['N/A']) + '\n'
            f'  Skipped: missing_end={tickets_missing_end}, inconsistent={tickets_inconsistent}, outlier={tickets_outlier}'
        )
        
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
        - Filter ONLY by incident_datetime (Thời gian ghi nhận sự việc)
        - NO fallback to completed_state_tracking_datetime or write_date
        - States: completed, dump, remix, swap
        
        Yêu cầu:
        - Chỉ lấy tickets có incident_datetime trong date range
        - Không dùng completed_state_tracking_datetime
        - Không dùng write_date
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        model = self.env['mrp.production']
        model_fields = model._fields

        base_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', 'in', ['completed', 'dump', 'remix', 'swap']),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        if station_id:
            base_domain.append(('vehicle_station_id', '=', station_id))

        # Log chi tiết domain và date range
        _logger.info(
            f'[AnalyticDashboard] ─────────────────────────────────────\n'
            f'[AnalyticDashboard] RETURN VOLUME CHART - Filter Domain:\n'
            f'  Base domain: {base_domain}\n'
            f'  Date range: {date_range}\n'
            f'  Station ID: {station_id}'
        )
        
        # CHỈ filter theo incident_datetime
        tickets = model.browse()
        if date_range:
            if 'incident_datetime' in model_fields:
                incident_domain = base_domain + [
                    ('incident_datetime', '>=', date_range['from']),
                    ('incident_datetime', '<=', date_range['to']),
                ]
                _logger.info(f'[AnalyticDashboard]   Searching ONLY with incident_datetime domain: {incident_domain}')
                tickets = model.search(incident_domain)
            else:
                _logger.warning('[AnalyticDashboard]   incident_datetime field not found! No tickets will be returned.')
                tickets = model.browse()
        else:
            tickets = model.search(base_domain)

        _logger.info(
            f'[AnalyticDashboard]   Total tickets found: {len(tickets)}\n'
            f'[AnalyticDashboard]   IDs: {sorted(tickets.ids)[:20]}{"..." if len(tickets) > 20 else ""}\n'
            f'[AnalyticDashboard] ─────────────────────────────────────'
        )
        
        # ============================================================================
        # KHỐI LƯỢNG BÊ TÔNG SỰ CỐ (RETURN VOLUME / INCIDENT VOLUME)
        # ============================================================================
        # Yêu cầu:
        # 1. Chart hiển thị: Remix, Dump, Swap (KHÔNG hiển thị Completed)
        # 2. Tính % = (Khối lượng sự cố) / (Khối lượng đã kết thúc) * 100
        #    - Khối lượng sự cố = Remix + Dump + Swap
        #    - Khối lượng đã kết thúc = Completed + Remix + Dump + Swap
        # ============================================================================
        
        # Separate tickets by state and collect IDs
        remix_tickets = tickets.filtered(lambda t: t.state_concrete == 'remix')
        dump_tickets = tickets.filtered(lambda t: t.state_concrete == 'dump')
        swap_tickets = tickets.filtered(lambda t: t.state_concrete == 'swap')
        completed_tickets = tickets.filtered(lambda t: t.state_concrete == 'completed')
        
        # Calculate volumes per state using product_qty from mrp.production
        remix_volume = sum(t.product_qty for t in remix_tickets)
        dump_volume = sum(t.product_qty for t in dump_tickets)
        swap_volume = sum(t.product_qty for t in swap_tickets)
        completed_volume = sum(t.product_qty for t in completed_tickets)

        # Khối lượng sự cố: CHỈ Remix + Dump + Swap (KHÔNG có Completed)
        total_incident_volume = remix_volume + dump_volume + swap_volume

        # Khối lượng đã kết thúc: Completed + Remix + Dump + Swap
        # (Bao gồm cả completed vì đây là mẫu số để tính %)
        total_finished_volume = completed_volume + remix_volume + dump_volume + swap_volume

        # Tính phần trăm: % sự cố so với tổng đã kết thúc
        # VD: Nếu có 10m³ completed, 2m³ remix, 1m³ dump, 1m³ swap
        #     → % = (2+1+1) / (10+2+1+1) * 100 = 4/14 * 100 = 28.6%
        percentage = (total_incident_volume / total_finished_volume * 100) if total_finished_volume > 0 else 0
        
        # Collect IDs for logging
        remix_ids = sorted(remix_tickets.ids)
        dump_ids = sorted(dump_tickets.ids)
        swap_ids = sorted(swap_tickets.ids)
        completed_ids = sorted(completed_tickets.ids)
        all_ids = sorted(tickets.ids)
        
        # Format IDs for display (show first 10, then count remaining)
        def format_ids(ids, max_show=10):
            if not ids:
                return '[]'
            if len(ids) <= max_show:
                return str(ids)
            shown = ids[:max_show]
            remaining = len(ids) - max_show
            return f"{shown}... (+{remaining} more)"
        
        # Show sample records with datetime for debugging
        sample_dump_details = []
        for ticket in dump_tickets[:3]:  # First 3 dump records
            incident_dt = getattr(ticket, 'incident_datetime', None)
            completed_dt = getattr(ticket, 'completed_state_tracking_datetime', None)
            sample_dump_details.append(
                f"    ID {ticket.id}: incident={incident_dt}, completed={completed_dt}, qty={ticket.product_qty}"
            )
        
        _logger.info(
            f'[AnalyticDashboard] Return Volume Chart:\n'
            f'  Remix: {len(remix_tickets)} records, {remix_volume} m³\n'
            f'    IDs: {format_ids(remix_ids)}\n'
            f'  Dump: {len(dump_tickets)} records, {dump_volume} m³\n'
            f'    IDs: {format_ids(dump_ids)}\n'
            f'{chr(10).join(sample_dump_details) if sample_dump_details else ""}\n'
            f'  Swap: {len(swap_tickets)} records, {swap_volume} m³\n'
            f'    IDs: {format_ids(swap_ids)}\n'
            f'  Completed: {len(completed_tickets)} records, {completed_volume} m³\n'
            f'    IDs: {format_ids(completed_ids, max_show=5)}\n'
            f'  ─────────────────────────────\n'
            f'  Khối lượng sự cố: {total_incident_volume} m³ ({len(remix_tickets) + len(dump_tickets) + len(swap_tickets)} records)\n'
            f'  Khối lượng đã kết thúc: {total_finished_volume} m³ ({len(tickets)} records)\n'
            f'  Phần trăm sự cố: {percentage:.1f}%\n'
            f'  ─────────────────────────────\n'
            f'  All Record IDs ({len(all_ids)} total): {format_ids(all_ids, max_show=20)}'
        )
        
        # Return ONLY incident states to frontend (remix, dump, swap)
        # Frontend will display these 3 values in the chart
        # The percentage is already calculated including completed volume
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
        - Filter ONLY by arrived_state_tracking_datetime (NO fallback)
        - States: arrived, unloading, return, completed, dump, remix, swap
        - Domain: [("mo_type", "=", "concrete"), ("arrived_state_tracking_datetime", ">=", ...), ("arrived_state_tracking_datetime", "<=", ...), ("state_concrete", "in", [...])]
        """
        import logging
        _logger = logging.getLogger(__name__)
        
        # CHỈ filter theo arrived_state_tracking_datetime (Thời gian Arrived)
        ticket_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', 'in', ['arrived', 'unloading', 'return', 'completed', 'dump', 'remix', 'swap']),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]

        if date_range:
            ticket_domain.append(('arrived_state_tracking_datetime', '>=', date_range['from']))
            ticket_domain.append(('arrived_state_tracking_datetime', '<=', date_range['to']))

        if station_id:
            ticket_domain.append(('vehicle_station_id', '=', station_id))

        _logger.info(f'[AnalyticDashboard] On-time Delivery - Domain: {ticket_domain}')
        tickets = self.env['mrp.production'].search(ticket_domain)
        _logger.info(f'[AnalyticDashboard] On-time Delivery - Found {len(tickets)} tickets')
        
        # Count on-time vs total
        # CHỈ dùng arrived_state_tracking_datetime (không có fallback)
        on_time_count = 0
        total_with_arrived = 0
        tickets_without_arrived = 0
        tickets_without_eta = 0

        for ticket in tickets:
            # CHỈ lấy arrived_state_tracking_datetime (không fallback)
            arrived_time = ticket.arrived_state_tracking_datetime
            
            if not arrived_time:
                tickets_without_arrived += 1
                continue

            # Only count tickets with ETA in denominator
            if not ticket.eta:
                tickets_without_eta += 1
                continue

            total_with_arrived += 1

            if arrived_time <= ticket.eta:
                on_time_count += 1

        percentage = (on_time_count / total_with_arrived * 100) if total_with_arrived > 0 else 0
        late_count = total_with_arrived - on_time_count

        _logger.info(
            f'[AnalyticDashboard] On-time Delivery Chart:\n'
            f'  Total tickets searched: {len(tickets)}\n'
            f'  Tickets with arrived & ETA: {total_with_arrived}\n'
            f'  On-time: {on_time_count} tickets ({percentage:.1f}%)\n'
            f'  Late: {late_count} tickets ({100-percentage:.1f}%)\n'
            f'  Skipped: without_arrived={tickets_without_arrived}, without_eta={tickets_without_eta}'
        )

        return round(percentage, 1)

    def _get_debug_data(self, station_id, date_range):
        """
        Get debug data: domains and record IDs for each chart/KPI
        Used when chart_debug=1 to show "View Records" buttons
        """
        debug_data = {}

        # Base domains for each data source
        model_fields = self.env['mrp.production']._fields

        # 1. KPIs - Sale Orders
        so_domain = [
            ('so_type', '=', 'concrete'),
            ('state', 'in', ('sale', 'planned', 'dispatching', 'done')),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        if date_range:
            so_domain.append(('date_order', '>=', date_range['from']))
            so_domain.append(('date_order', '<=', date_range['to']))
        if station_id:
            so_domain.append(('concrete_station_id', '=', station_id))

        so_ids = self.env['sale.order'].search(so_domain).ids
        debug_data['kpis'] = {
            'model': 'sale.order',
            'domain': so_domain,
            'record_ids': so_ids,
            'count': len(so_ids),
        }

        # 2. Trips per vehicle - CHỈ completed_state_tracking_datetime
        trips_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', '=', 'completed'),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        if date_range:
            trips_domain.append(('completed_state_tracking_datetime', '>=', date_range['from']))
            trips_domain.append(('completed_state_tracking_datetime', '<=', date_range['to']))
        if station_id:
            trips_domain.append(('vehicle_station_id', '=', station_id))

        trips_ids = self.env['mrp.production'].search(trips_domain).ids
        debug_data['trips_per_vehicle'] = {
            'model': 'mrp.production',
            'domain': trips_domain,
            'record_ids': trips_ids,
            'count': len(trips_ids),
        }

        # 3. Concrete lifetime - CHỈ loaded_datetime
        lifetime_domain = [
            ('mo_type', '=', 'concrete'),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        if date_range:
            lifetime_domain.append(('loaded_datetime', '>=', date_range['from']))
            lifetime_domain.append(('loaded_datetime', '<=', date_range['to']))
        if station_id:
            lifetime_domain.append(('vehicle_station_id', '=', station_id))

        lifetime_ids = self.env['mrp.production'].search(lifetime_domain).ids
        debug_data['concrete_lifetime'] = {
            'model': 'mrp.production',
            'domain': lifetime_domain,
            'record_ids': lifetime_ids,
            'count': len(lifetime_ids),
        }

        # 4. Vehicle cycle time - Assigned & completed tickets
        cycle_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', '=', 'completed'),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        if date_range:
            cycle_domain.append(('assigned_datetime', '>=', date_range['from']))
            cycle_domain.append(('assigned_datetime', '<=', date_range['to']))
        if station_id:
            cycle_domain.append(('vehicle_station_id', '=', station_id))

        cycle_ids = self.env['mrp.production'].search(cycle_domain).ids
        debug_data['vehicle_cycle_time'] = {
            'model': 'mrp.production',
            'domain': cycle_domain,
            'record_ids': cycle_ids,
            'count': len(cycle_ids),
        }

        # 5. Return volume - CHỈ incident_datetime
        return_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', 'in', ['completed', 'dump', 'remix', 'swap']),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        if date_range:
            return_domain.append(('incident_datetime', '>=', date_range['from']))
            return_domain.append(('incident_datetime', '<=', date_range['to']))
        if station_id:
            return_domain.append(('vehicle_station_id', '=', station_id))

        return_ids = self.env['mrp.production'].search(return_domain).ids
        debug_data['return_volume'] = {
            'model': 'mrp.production',
            'domain': return_domain,
            'record_ids': return_ids,
            'count': len(return_ids),
        }

        # 6. On-time delivery - CHỈ arrived_state_tracking_datetime
        ontime_domain = [
            ('mo_type', '=', 'concrete'),
            ('state_concrete', 'in', ['arrived', 'unloading', 'return', 'completed', 'dump', 'remix', 'swap']),
            ('company_id', 'in', self._get_allowed_company_ids()),
        ]
        if date_range:
            ontime_domain.append(('arrived_state_tracking_datetime', '>=', date_range['from']))
            ontime_domain.append(('arrived_state_tracking_datetime', '<=', date_range['to']))
        if station_id:
            ontime_domain.append(('vehicle_station_id', '=', station_id))

        ontime_ids = self.env['mrp.production'].search(ontime_domain).ids
        debug_data['on_time_delivery'] = {
            'model': 'mrp.production',
            'domain': ontime_domain,
            'record_ids': ontime_ids,
            'count': len(ontime_ids),
        }

        return debug_data
