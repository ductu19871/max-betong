from odoo import models, fields, api

class OutputDashboard(models.AbstractModel):
    _name = 'max_betong.output.dashboard'
    _description = 'Dashboard Báo Cáo Sản Lượng'

    # @staticmethod
    # def flat_plan_lines_groups_by_key(plan_lines_groups, key, chart_amount_unit):
    #     return [i[key] for i in plan_lines_groups]
    
    # # @staticmethod
    # # def get_value_el_by_key(plan_lines_groups, key):
    # #     return plan_lines_groups[-1][key]
    
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
    

    # @staticmethod
    # def get_el_by_today(plan_lines_groups, s_curve_mode):
    #     for el in plan_lines_groups:
    #         str_today = str(fields.Date.today())
    #         # if el['__range']['from_date']['from'] <= str_today:
    #         #     return el
    #         # if el['__range']['from_date:day']['from'] <= str_today < el['__range']['from_date:day']['to']:
    #         #     return el
    #         if el['__range']['from_date:day']['from'] <= str_today < el['__range']['to_date:day']['from']:
    #             return el
    #         # if el['__range']['from_date:%s'%s_curve_mode]['from'] <= str_today :
    #         #     return el

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
            # Lấy range của from_date và to_date với hậu tố :day
            range_from = el.get('__range', {}).get(f'from_date{key_group}', {})
            # range_to = el.get('__range', {}).get('to_date:day', {})
            
            # Logic: Ngày bắt đầu của nhóm này <= Hôm nay < Ngày bắt đầu của nhóm kế tiếp
            if range_from.get('from') <= str_today:
                return el
        
        return None
    

    @api.model
    def get_dashboard_data(self, filters=None):
        """Mock data for the dashboard."""
        chart_amount_unit = self.env.company.chart_amount_unit or 'billion'
        s_curve_mode = self.env.company.s_curve_mode or 'month'
        type_ = 'customer'
        customer_partner_id = None
        project_id = None
        subcontractor_partner_id = None
        contract_ids = None
        # plan_domain = [('state', '=', 'confirm'), ('type', '=', type_), ('s_curve_mode', '=', s_curve_mode)]
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
        
        if s_curve_mode == 'week':
            groupby = ['from_date:week']
        else:
            groupby = ['from_date:month']
        key_group = ':day'
        key_group = f':{s_curve_mode}'
        plan_lines_groups = self.env["deliverable.payment.plan.line"].read_group(
            domain=[('plan_id', 'in', plans.ids)],
            fields=['from_date', 'plan_accumulated_amount', 'actual_accumulated_amount', 'plan_accumulated_ipc_amount', 'actual_accumulated_ipc_amount', 'actual_accumulated_paid_amount',
                    'actual_percentage', 'actual_amount', 'actual_percentage_accumulated',  'actual_paid_amount',
                    'plan_percentage_accumulated'
                    ],  # Fields to retrieve or aggregate
            groupby=[f'from_date{key_group}', f'to_date{key_group}']            # The field to group by
            # groupby=groupby          # The field to group by
        )
        # plan = plans[-1:]
        contracts = plans.get_contracts()
        start = min(contracts.mapped('contract_start_date'), default=0)
        start = start.strftime('%d/%m/%Y') if start else ''
        end = max(contracts.mapped('contract_end_date'), default=0)
        end = end.strftime('%d/%m/%Y') if end else ''
        today_el = self.get_el_by_today(plan_lines_groups, key_group)
        delayed_value = today_el['plan_accumulated_amount'] - today_el['actual_accumulated_amount'] # chậm tiến độ
        delayed_payment = today_el['plan_accumulated_ipc_amount'] - today_el['actual_accumulated_ipc_amount']
        return {
            'contract_info': {
                'value': self.convert_val_to_string(sum(plans.mapped('total_project_amount')), chart_amount_unit), #contract.amount_total,#plan.total_project_amount,
                'name': ', '.join(str(i) for i in contracts.mapped('contract_ref_no')),
                'time': f'{start} - {end}',
                'plan_percent': self.get_value_el_by_key(today_el, 'plan_percentage_accumulated', None),#today_el['plan_percentage_accumulated'],
                'actual_percent': self.get_value_el_by_key(today_el, 'actual_percentage', None),
                'delayed_value': self.convert_val_to_string(delayed_value, chart_amount_unit),
                'delayed_payment': self.convert_val_to_string(delayed_payment, chart_amount_unit) 
            },
            'summary': {
                'plan_vol': self.get_value_el_by_key(today_el, 'plan_accumulated_amount', chart_amount_unit),
                'actual_vol': self.get_value_el_by_key(today_el, 'actual_accumulated_amount', chart_amount_unit),
                'plan_pay': self.get_value_el_by_key(today_el, 'plan_accumulated_ipc_amount', chart_amount_unit),
                'actual_pay': self.get_value_el_by_key(today_el, 'actual_accumulated_paid_amount', chart_amount_unit),
            },
            'table_columns': [
                'Chỉ tiêu', *self.flat_plan_lines_groups_by_key(plan_lines_groups, f'from_date{key_group}', is_not_number=True)
            ],
            # 'table_data': [
            #     ['Tỷ lệ % SL', '5%', '8%', '10%', '12%', '10%', '8%', '9%', '11%'],
            #     ['Giá trị SL', '5.0', '8.0', '10.0', '12.0', '10.0', '8.0', '9.0', '11.0'],
            #     ['% Lũy kế SL', '5%', '13%', '23%', '35%', '45%', '53%', '62%', '73%'],
            #     ['Giá trị lũy kế SL', '5.0', '13.0', '23.0', '35.0', '45.0', '53.0', '62.0', '73.0'],
            #     ['Giá trị thanh toán', '3.0', '7.0', '5.0', '8.0', '6.0', '4.0', '7.0', '9.0'],
            #     ['Lũy kế thanh toán', '3.0', '10.0', '15.0', '23.0', '29.0', '33.0', '40.0', '49.0']
            # ],
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

    # @api.model
    # def get_dashboard_data(self,  filters=None):
    #     """
    #     Truy vấn dữ liệu thực tế từ plan_id cụ thể để fill vào Dashboard.
    #     Nếu không có plan_id, lấy bản ghi 'confirm' mới nhất.
    #     """
    #     plan_id = 1
    #     # 1. Xác định Plan cần lấy dữ liệu
    #     domain = [('id', '=', plan_id)] if plan_id else [('state', '=', 'confirm')]
    #     plan = self.search(domain, limit=1, order='create_date desc')
        
    #     if not plan:
    #         return {} # Hoặc trả về mockup trống

    #     # 2. Lấy danh sách các dòng đã được sắp xếp theo thời gian
    #     lines = plan.line_ids.sorted('from_date')
        
    #     # 3. Chuẩn bị các mảng dữ liệu cho Chart và Table
    #     labels = [l.from_date.strftime("T%m/%Y") for l in lines]
        
    #     # Dữ liệu sản lượng (Actual Amount)
    #     actual_amounts = [l.actual_amount for l in lines]
    #     actual_acc_amounts = [l.actual_accumulated_amount for l in lines]
        
    #     # Dữ liệu kế hoạch (Plan Amount)
    #     plan_amounts = [l.plan_amount for l in lines]
    #     plan_acc_amounts = [l.plan_accumulated_amount for l in lines]
        
    #     # Dữ liệu nghiệm thu (IPC)
    #     actual_ipc_amounts = [l.actual_ipc_amount for l in lines]
    #     actual_acc_ipc_amounts = [l.actual_accumulated_ipc_amount for l in lines]
        
    #     # Dữ liệu thanh toán (Paid)
    #     actual_paid_amounts = [l.actual_paid_amount for l in lines]
    #     actual_acc_paid_amounts = [l.actual_accumulated_paid_amount for l in lines]

    #     # 4. Tính toán các chỉ số tóm tắt (Summary)
    #     last_line = lines[-1] if lines else False
    #     current_acc_plan = last_line.plan_percentage_accumulated if last_line else 0
    #     current_acc_actual = last_line.actual_percentage_accumulated if last_line else 0
        
    #     return {
    #         'contract_info': {
    #             'name': plan.name or 'N/A',
    #             'value': f"{plan.total_project_amount:,.0f} {plan.currency_id.symbol}",
    #             'time': f"{plan.from_date.strftime('%d/%m/%y')} - {plan.to_date.strftime('%d/%m/%y')}",
    #             'plan_percent': f"{current_acc_plan:.1f}%",
    #             'actual_percent': f"{current_acc_actual:.1f}%",
    #             'delayed_value': f"{(plan.total_project_amount * (current_acc_plan - current_acc_actual) / 100):,.0f} {plan.currency_id.symbol}",
    #             'delayed_payment': f"{(sum(actual_ipc_amounts) - sum(actual_paid_amounts)):,.0f} {plan.currency_id.symbol}"
    #         },
    #         'summary': {
    #             'plan_vol': f"{sum(plan_amounts):,.0f}",
    #             'actual_vol': f"{sum(actual_amounts):,.0f}",
    #             'plan_pay': f"{sum(actual_ipc_amounts):,.0f}", # Giá trị đã nghiệm thu
    #             'actual_pay': f"{sum(actual_paid_amounts):,.0f}", # Tiền thực tế đã về
    #         },
    #         'table_columns': ['Chỉ tiêu'] + labels,
    #         'table_data': [
    #             ['Sản lượng thực tế (Kỳ)'] + [f"{v:,.1f}" for v in actual_amounts],
    #             ['Lũy kế sản lượng'] + [f"{v:,.1f}" for v in actual_acc_amounts],
    #             ['Nghiệm thu thực tế (IPC)'] + [f"{v:,.1f}" for v in actual_ipc_amounts],
    #             ['Lũy kế nghiệm thu'] + [f"{v:,.1f}" for v in actual_acc_ipc_amounts],
    #             ['Thanh toán thực tế (Paid)'] + [f"{v:,.1f}" for v in actual_paid_amounts],
    #             ['Lũy kế thanh toán'] + [f"{v:,.1f}" for v in actual_acc_paid_amounts]
    #         ],
    #         'chart': {
    #             'labels': labels,
    #             'datasets': [
    #                 {'label': '1. Kế hoạch (Kỳ)', 'data': plan_amounts, 'borderColor': '#2196f3', 'fill': False},
    #                 {'label': '2. Sản lượng thực tế (Lũy kế)', 'data': actual_acc_amounts, 'borderColor': '#4caf50', 'fill': False},
    #                 {'label': '3. Nghiệm thu (Lũy kế)', 'data': actual_acc_ipc_amounts, 'borderColor': '#9c27b0', 'fill': False},
    #                 {'label': '4. Thanh toán (Lũy kế)', 'data': actual_acc_paid_amounts, 'borderColor': '#f44336', 'fill': False}
    #             ]
    #         }
    #     }