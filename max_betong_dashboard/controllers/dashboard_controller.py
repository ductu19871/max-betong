# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class ConcreteDashboardController(http.Controller):
    """
    Controller for Concrete Dashboard API endpoints
    """

    @http.route('/concrete/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self, params=None):
        """
        API endpoint to get all dashboard data with pagination
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard.get_dashboard_data(params or {})

    @http.route('/concrete/dashboard/orders', type='json', auth='user')
    def get_orders(self, params=None):
        """
        API endpoint to get orders data with pagination
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard._get_orders_data(params or {})

    @http.route('/concrete/dashboard/loads', type='json', auth='user')
    def get_loads(self, params=None, selected_order_id=None):
        """
        API endpoint to get loads data with pagination
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard._get_loads_data(params or {}, selected_order_id)

    @http.route('/concrete/dashboard/vehicles', type='json', auth='user')
    def get_vehicles(self, params=None):
        """
        API endpoint to get vehicles data with pagination
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard._get_vehicles_data(params or {})

    @http.route('/concrete/dashboard/tickets', type='json', auth='user')
    def get_tickets(self, params=None):
        """
        API endpoint to get tickets data with pagination
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard._get_tickets_data(params or {})

    @http.route('/concrete/dashboard/stations', type='json', auth='user')
    def get_stations(self):
        """
        API endpoint to get all stations
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard._get_stations_data()

    @http.route('/concrete/dashboard/assign_ticket', type='json', auth='user')
    def assign_ticket(self, load_id, vehicle_id):
        """
        API endpoint to assign a ticket (load + vehicle)
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard.assign_ticket(load_id, vehicle_id)

    @http.route('/concrete/dashboard/split_load', type='json', auth='user')
    def split_load(self, order_id):
        """
        API endpoint to split load for an order
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard.split_load(order_id)

    @http.route('/concrete/dashboard/delete_load', type='json', auth='user')
    def delete_load(self, load_id):
        """
        API endpoint to delete a load
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard.delete_load(load_id)

    @http.route('/concrete/dashboard/update_order_station', type='json', auth='user')
    def update_order_station(self, order_id, station_id):
        """
        API endpoint to update order station
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard.update_order_station(order_id, station_id)

    @http.route('/concrete/dashboard/update_load_station', type='json', auth='user')
    def update_load_station(self, load_id, station_id):
        """
        API endpoint to update load station
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard.update_load_station(load_id, station_id)

    @http.route('/concrete/dashboard/permissions', type='json', auth='user')
    def get_permissions(self):
        """
        API endpoint to get user permissions
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard.get_user_permissions()

    @http.route('/concrete/dashboard/update_vehicle_station', type='json', auth='user')
    def update_vehicle_station(self, vehicle_id, station_id):
        """
        API endpoint to update vehicle station
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard.update_vehicle_station(vehicle_id, station_id)

    @http.route('/concrete/dashboard/update_vehicle_state', type='json', auth='user')
    def update_vehicle_state(self, vehicle_id, state_concrete):
        """
        API endpoint to update vehicle state
        """
        dashboard = request.env['concrete.dashboard']
        return dashboard.update_vehicle_state(vehicle_id, state_concrete)
