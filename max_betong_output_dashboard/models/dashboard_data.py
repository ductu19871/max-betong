from odoo import models, fields, api

class OutputDashboard(models.AbstractModel):
    _name = 'max_betong.output.dashboard'
    _description = 'Dashboard Báo Cáo Sản Lượng'

    
    @staticmethod
    def flat_plan_lines_groups_by_key(plan_lines_groups, key, chart_amount_unit=None, precision=None, is_not_number=False):
        """
        Lấy giá trị từ list mapping. 
        - Nếu không có unit: Trả về giá trị gốc (không làm tròn).
        - Nếu có unit: Quy đổi đơn vị và làm tròn theo precision.
        """
        # Trường hợp 1: Không có unit -> Trả về nguyên bản từ kết quả query
        if is_not_number:
            return [i.get(key) for i in plan_lines_groups]

        # Trường hợp 2: Có unit -> Xử lý tính toán
        unit_map = {
            'vnd': (1, 0),
            'million': (1_000_000, 0),
            'billion': (1_000_000_000, 2)
        }
        PERCENT_FORMAT = (1, 2)
        divisor, default_precision = unit_map.get(chart_amount_unit, chart_amount_unit) or PERCENT_FORMAT
        if precision==None:
            precision = default_precision
        # Ép kiểu float, chia đơn vị và làm tròn
        return [round(float(i.get(key) or 0) / divisor, precision) for i in plan_lines_groups]
    
    # @staticmethod
    def get_value_el_by_key(self, el, key, chart_amount_unit):
        # 1. Lấy giá trị gốc (mặc định là 0 nếu không có key)
        val = el.get(key, 0)
        return self.convert_val_to_string(val, chart_amount_unit)
    

    @staticmethod
    def convert_val_to_string(val, chart_amount_unit, precision=None):
        # 1. Lấy giá trị gốc (mặc định là 0 nếu không có key)
        if not chart_amount_unit:
            if precision==None:
                precision=2
            return f"{val:,.{precision}f}"
        # 2. Định nghĩa bảng quy đổi và nhãn hiển thị
        # Hệ số chia và Tên đơn vị tương ứng
        unit_map = {
            'vnd': (1, 'đồng', 0),
            'million': (1_000_000, 'triệu đồng', 0),
            'billion': (1_000_000_000, 'tỷ đồng', 2)
        }
    
        # 3. Lấy cấu hình dựa trên chart_amount_unit, mặc định là 'billion'
        divisor, label, default_precision = unit_map.get(chart_amount_unit, unit_map['billion'])
        if precision==None:
                precision=default_precision
        # 4. Tính toán giá trị đã quy đổi
        converted_val = val / divisor
        return f"{converted_val:,.{precision}f} {label}"

    @staticmethod
    def get_el_by_today(plan_lines_groups, key_group):
        # 1. Sắp xếp danh sách từ cũ đến mới dựa trên ngày bắt đầu (from)
        # Ép kiểu về chuỗi rỗng nếu None để tránh lỗi khi so sánh (sort)
        sorted_groups = sorted(
            plan_lines_groups, 
            key=lambda x: x.get('__range', {}).get(f'from_date{key_group}', {}).get('from') or '',
            reverse=True

        )

        # 2. Lấy ngày hôm nay (YYYY-MM-DD)
        str_today = str(fields.Date.today())
        
        # 3. Duyệt qua danh sách đã sắp xếp, gặp cái đầu tiên thỏa là return ngay
        for el in sorted_groups:
            range_from = el.get('__range', {}).get(f'from_date{key_group}', {})
            if range_from.get('from') <= str_today:
                return el
        
        return None
    

    def get_values_filters(self):

        type_ = 'customer'
        customer_partner_id = None
        project_id = None
        subcontractor_partner_id = None
        contract_ids = None

        return type_, customer_partner_id, project_id, subcontractor_partner_id, contract_ids



    @api.model
    def get_dashboard_data(self, filters=None):
        """Mock data for the dashboard."""
        chart_amount_unit = self.env.company.chart_amount_unit or 'billion'
        s_curve_mode = self.env.company.s_curve_mode or 'month'

        type_, customer_partner_id, project_id, subcontractor_partner_id, contract_ids = \
            self.get_values_filters()
        
        plan_domain = [('type', '=', type_), ('s_curve_mode', '=', s_curve_mode)]
        if contract_ids:
            if type_ == 'customer' :
                plan_domain += [('customer_contract_id', 'in',  contract_ids)]
            else:
                plan_domain += [('subcontractor_contract_id', 'in',  contract_ids)]
        else:
            if project_id:
                plan_domain += [('project_id', '=', project_id)]
            if customer_partner_id and  type_ == 'customer':
                plan_domain += [('partner_id', '=', customer_partner_id)]
            elif subcontractor_partner_id:
                plan_domain += [('partner_id', '=', subcontractor_partner_id)]

        plans = self.env["deliverable.payment.plan"].search(plan_domain)
        
        # key_group = ':day'
        key_group = f':{s_curve_mode}'
        plan_lines_groups = self.env["deliverable.payment.plan.line"].read_group(
            domain=[('plan_id', 'in', plans.ids)],
            fields=['from_date', 'plan_accumulated_amount', 'actual_accumulated_amount', 'plan_accumulated_ipc_amount', 'actual_accumulated_ipc_amount', 'actual_accumulated_paid_amount',
                    'actual_percentage', 'actual_amount', 'actual_percentage_accumulated',  'actual_paid_amount',
                    'plan_percentage_accumulated'
                    ], 
            groupby=[f'from_date{key_group}']  
        )
        contracts = plans.get_contracts()
        start = min(contracts.mapped('contract_start_date'), default=0)
        start = start.strftime('%d/%m/%Y') if start else ''
        end = max(contracts.mapped('contract_end_date'), default=0)
        end = end.strftime('%d/%m/%Y') if end else ''
        today_el = self.get_el_by_today(plan_lines_groups, key_group)
        delayed_value = today_el['plan_accumulated_amount'] - today_el['actual_accumulated_amount'] # chậm tiến độ
        delayed_payment = today_el['plan_accumulated_ipc_amount'] - today_el['actual_accumulated_ipc_amount'] # chênh lệch nghiệm thu
        return {
            'contract_info': {
                'value': self.convert_val_to_string(sum(plans.mapped('total_project_amount')), chart_amount_unit), #contract.amount_total,#plan.total_project_amount,
                'name': ', '.join(str(i) for i in contracts.mapped('contract_ref_no')),
                'time': f'{start} - {end}',
                'plan_percent': self.get_value_el_by_key(today_el, 'plan_percentage_accumulated', None),#today_el['plan_percentage_accumulated'],
                'actual_percent': self.get_value_el_by_key(today_el, 'actual_percentage', None),
                'delayed_value': self.convert_val_to_string(delayed_value, chart_amount_unit),
                'delayed_payment': self.convert_val_to_string(delayed_payment, chart_amount_unit) # chênh lệch nghiệm thu
            },
            'summary': {
                'plan_vol': self.get_value_el_by_key(today_el, 'plan_accumulated_amount', chart_amount_unit),
                'actual_vol': self.get_value_el_by_key(today_el, 'actual_accumulated_amount', chart_amount_unit),
                'plan_pay': self.get_value_el_by_key(today_el, 'actual_accumulated_ipc_amount', chart_amount_unit), #  thay bằng nghiệm thu thực tế lũy kế
                'actual_pay': self.get_value_el_by_key(today_el, 'actual_accumulated_paid_amount', chart_amount_unit),
            },
            'table_columns': [
                'Chỉ tiêu', *self.flat_plan_lines_groups_by_key(plan_lines_groups, f'from_date{key_group}', is_not_number=True)
            ],
            'table_data': [
                ['Tỷ lệ % SL',  *self.flat_plan_lines_groups_by_key(plan_lines_groups, 'actual_percentage')],
                ['Giá trị SL', *self.flat_plan_lines_groups_by_key(plan_lines_groups, 'actual_amount', chart_amount_unit)],
                ['% Lũy kế SL', *self.flat_plan_lines_groups_by_key(plan_lines_groups, 'actual_percentage_accumulated')],
                ['Giá trị lũy kế SL', *self.flat_plan_lines_groups_by_key(plan_lines_groups, 'actual_accumulated_amount', chart_amount_unit)],
                ['Giá trị thanh toán', *self.flat_plan_lines_groups_by_key(plan_lines_groups, 'actual_paid_amount', chart_amount_unit)],
                ['Lũy kế thanh toán', *self.flat_plan_lines_groups_by_key(plan_lines_groups, 'actual_accumulated_paid_amount', chart_amount_unit)]
            ],
            'chart': {
                'labels': self.flat_plan_lines_groups_by_key(plan_lines_groups, f'from_date{key_group}', is_not_number=True),
                'datasets': [
                    {'label': '1. Sản lượng kế hoạch', 'data':  self.flat_plan_lines_groups_by_key(plan_lines_groups, 'plan_accumulated_amount', chart_amount_unit), 'borderColor': '#2196f3', 'backgroundColor': '#2196f3', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#2196f3', 'pointRadius': 4, 'tension': 0.1, 'fill': False},
                    {'label': '2. Sản lượng thực tế', 'data': self.flat_plan_lines_groups_by_key(plan_lines_groups, 'actual_accumulated_amount', chart_amount_unit), 'borderColor': '#4caf50', 'backgroundColor': '#4caf50', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#4caf50', 'pointRadius': 4, 'tension': 0.1, 'fill': False},
                    {'label': '3. Giá trị nghiệm thu kế hoạch', 'data': self.flat_plan_lines_groups_by_key(plan_lines_groups, 'plan_accumulated_ipc_amount', chart_amount_unit), 'borderColor': '#ff9800', 'backgroundColor': '#ff9800', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#ff9800', 'pointRadius': 4, 'borderDash': [5, 5], 'tension': 0.1, 'fill': False},
                    {'label': '4. Giá trị nghiệm thu thực tế', 'data': self.flat_plan_lines_groups_by_key(plan_lines_groups, 'actual_accumulated_ipc_amount', chart_amount_unit), 'borderColor': '#9c27b0', 'backgroundColor': '#9c27b0', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#9c27b0', 'pointRadius': 4, 'tension': 0.1, 'fill': False},
                    {'label': '5. Thanh toán thực tế', 'data': self.flat_plan_lines_groups_by_key(plan_lines_groups, 'actual_accumulated_paid_amount', chart_amount_unit), 'borderColor': '#f44336', 'backgroundColor': '#f44336', 'pointBackgroundColor': '#ffffff', 'pointBorderColor': '#f44336', 'pointRadius': 4, 'tension': 0.1, 'fill': False}
                ]
            }
        }

  