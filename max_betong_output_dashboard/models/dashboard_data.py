from odoo import models, fields, api

class OutputDashboard(models.AbstractModel):
    _name = 'max_betong.output.dashboard'
    _description = 'Dashboard Báo Cáo Sản Lượng'

    @api.model
    def get_dashboard_data(self, filters=None):
        """Mock data for the dashboard."""
        return {
            'contract_info': {
                'value': '100.0 Tỷ đồng',
                'name': 'Hợp đồng Kết cấu',
                'time': '01/01/2026 - 31/12/2026',
                'plan_percent': '73.0%',
                'actual_percent': '63.0%',
                'delayed_value': '10.0 Tỷ đồng',
                'delayed_payment': '-4.5 Tỷ đồng'
            },
            'summary': {
                'plan_vol': '73.0 Tỷ đồng',
                'actual_vol': '63.0 Tỷ đồng',
                'plan_pay': '49.0 Tỷ đồng',
                'actual_pay': '39.5 Tỷ đồng',
            },
            'table_columns': [
                'Chỉ tiêu', 'T01/2026', 'T02/2026', 'T03/2026', 'T04/2026', 
                'T05/2026', 'T06/2026', 'T07/2026', 'T08/2026'
            ],
            'table_data': [
                ['Tỷ lệ % SL', '5%', '8%', '10%', '12%', '10%', '8%', '9%', '11%'],
                ['Giá trị SL', '5.0', '8.0', '10.0', '12.0', '10.0', '8.0', '9.0', '11.0'],
                ['% Lũy kế SL', '5%', '13%', '23%', '35%', '45%', '53%', '62%', '73%'],
                ['Giá trị lũy kế SL', '5.0', '13.0', '23.0', '35.0', '45.0', '53.0', '62.0', '73.0'],
                ['Giá trị thanh toán', '3.0', '7.0', '5.0', '8.0', '6.0', '4.0', '7.0', '9.0'],
                ['Lũy kế thanh toán', '3.0', '10.0', '15.0', '23.0', '29.0', '33.0', '40.0', '49.0']
            ],
            'chart': {
                'labels': ['T01/2026', 'T02/2026', 'T03/2026', 'T04/2026', 'T05/2026', 'T06/2026', 'T07/2026', 'T08/2026'],
                'datasets': [
                    {'label': '1. Sản lượng kế hoạch', 'data': [10, 27, 50, 75, 102, 128, 150, 172], 'borderColor': '#2196f3', 'backgroundColor': '#2196f3', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#2196f3', 'pointRadius': 4, 'tension': 0.1, 'fill': False},
                    {'label': '2. Sản lượng thực tế', 'data': [8, 24, 44, 66, 89, 109, 131, 151], 'borderColor': '#4caf50', 'backgroundColor': '#4caf50', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#4caf50', 'pointRadius': 4, 'tension': 0.1, 'fill': False},
                    {'label': '3. Giá trị nghiệm thu kế hoạch', 'data': [7, 22, 42, 62, 86, 107, 126, 145], 'borderColor': '#ff9800', 'backgroundColor': '#ff9800', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#ff9800', 'pointRadius': 4, 'borderDash': [5, 5], 'tension': 0.1, 'fill': False},
                    {'label': '4. Giá trị nghiệm thu thực tế', 'data': [6, 20, 36, 56, 75, 95, 112, 131], 'borderColor': '#9c27b0', 'backgroundColor': '#9c27b0', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#9c27b0', 'pointRadius': 4, 'tension': 0.1, 'fill': False},
                    {'label': '5. Thanh toán thực tế', 'data': [4, 14, 27, 43, 58, 72, 87, 100], 'borderColor': '#f44336', 'backgroundColor': '#f44336', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#f44336', 'pointRadius': 4, 'tension': 0.1, 'fill': False}
                ]
            }
        }
