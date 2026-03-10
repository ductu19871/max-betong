# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class AnalyticDashboardController(http.Controller):

    @http.route('/concrete/analytic/get_data', type='json', auth='user')
    def get_analytic_data(self, station_id=None, time_filter='today', date_from=None, date_to=None, **kwargs):
        """
        Return analytics data based on filters
        
        Args:
            station_id: Station ID to filter (None = all stations)
            time_filter: 'today', 'week', 'month', 'quarter', 'year', 'custom'
            date_from: Start date for custom filter (YYYY-MM-DD format)
            date_to: End date for custom filter (YYYY-MM-DD format)
        """
        dashboard = request.env['analytic.dashboard']
        return dashboard.get_analytic_data(
            station_id=station_id,
            time_filter=time_filter or 'today',
            date_from=date_from,
            date_to=date_to,
            allowed_company_ids=kwargs.get('allowed_company_ids', [])
        )

