from odoo import models, fields, api
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

# class SaleOrder(models.Model):
#     _inherit = 'sale.order'

#     task_deliverable_ids = fields.One2many('project.progress.report', 'sale_order_id')


class OrderLineStockMixin(models.AbstractModel):
    _name = 'order.line.stock.mixin'
    _description = 'Mixin to calculate delivered qty in period via stock moves'

    def get_delivered_in_period(self, from_date, to_date):
        """
        Hàm dùng chung để tính số lượng thực tế dịch chuyển trong kỳ,
        có trừ đi hàng trả (Returns).
        """
        self.ensure_one()
        
        # 1. Xác định field liên kết và hướng kho tùy theo model
        if self._name == 'sale.order.line':
            line_field = 'sale_line_id'
            # Bán hàng: Xuất (Internal -> Customer) là [+], Nhập trả (Customer -> Internal) là [-]
            # out_usage, in_usage = 'internal', 'customer'
        else:
            line_field = 'purchase_line_id'
            # Mua hàng: Nhập (Supplier -> Internal) là [+], Trả NCC (Internal -> Supplier) là [-]
            # out_usage, in_usage = 'supplier', 'internal'

        # 2. Tìm các Stock Moves đã hoàn thành trong khoảng thời gian
        domain = [
            (line_field, '=', self.id),
            ('state', '=', 'done'),
            ('date', '>=', from_date),
            ('date', '<=', to_date),
            ('origin_returned_move_id', '=', False)
        ]
        moves = self.env['stock.move'].search(domain)

        total_qty = 0.0
        for move in moves:
            # Quy đổi số lượng move về đơn vị tính của Order Line
            qty = move.product_uom._compute_quantity(move.product_qty, self.product_uom)
            return_qty = sum(move.returned_move_ids.filtered(lambda move: move.state == 'done').mapped('product_qty'))
            total_qty = qty - return_qty
            # 3. Logic cộng trừ dựa trên hướng kho
            # Trường hợp Thuận (Giao hàng/Nhận hàng)
            # if move.location_id.usage == out_usage and move.location_dest_id.usage == in_usage:
            #     total_qty += qty
            # # Trường hợp Nghịch (Trả hàng)
            # elif move.location_id.usage == in_usage and move.location_dest_id.usage == out_usage:
            #     total_qty -= qty
        return total_qty

    def get_ordered_qty(self):
        """Hàm bổ trợ lấy số lượng đặt hàng đúng theo model"""
        self.ensure_one()
        return self.product_uom_qty if self._name == 'sale.order.line' else self.product_qty
    
class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = ['sale.order.line', 'order.line.stock.mixin']

class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'order.line.stock.mixin']
     
class DeliverablePaymentPlan(models.Model):
    _name = "deliverable.payment.plan"
    name = fields.Char(required=True)
    type = fields.Selection([
        ('customer', 'Customer Contract'),
        ('subcontract', 'Subcontractor Contract')
    ], required=True)

    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)

    customer_contract_id = fields.Many2one("sale.order")
    subcontractor_contract_id = fields.Many2one("purchase.order")
    partner_id = fields.Many2one("res.partner", compute="_compute_partner", store=True)
    project_id = fields.Many2one("project.project", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id.id
    )

    line_ids = fields.One2many("deliverable.payment.plan.line", "plan_id")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel'),
    ], default='draft')

    total_project_amount = fields.Monetary(
        string="Total Project Amount",
        compute="_compute_total_project_amount",
        store=True,
        currency_field="currency_id"
    )
    s_curve_mode = fields.Selection([
        ('month', 'Month'),
        ('week', 'Week')
    ], default= lambda self: self.env.company.s_curve_mode, readonly=1)

    @api.depends("type","customer_contract_id.partner_id","subcontractor_contract_id.partner_id")
    def _compute_partner(self):
        for rec in self:
            rec.partner_id = rec.customer_contract_id.partner_id if rec.type=='customer' else rec.subcontractor_contract_id.partner_id

    @api.depends("type", "customer_contract_id.amount_total", "subcontractor_contract_id.amount_total")
    def _compute_total_project_amount(self):
        for rec in self:
            if rec.type == 'customer' and rec.customer_contract_id:
                rec.total_project_amount = rec.customer_contract_id.amount_total
                rec.currency_id = rec.customer_contract_id.currency_id
            elif rec.type == 'subcontract' and rec.subcontractor_contract_id:
                rec.total_project_amount = rec.subcontractor_contract_id.amount_total
                rec.currency_id = rec.subcontractor_contract_id.currency_id
            else:
                rec.total_project_amount = 0.0

    def action_generate_lines(self):
        for rec in self:
            if rec.line_ids:
                raise UserError("Lines already exist")
            if not rec.from_date or not rec.to_date:
                raise UserError("Missing date")

            lines = []
            current = rec.from_date

            if rec.s_curve_mode == 'month':
                while current <= rec.to_date:
                    start = current.replace(day=1)
                    end = (start + relativedelta(months=1)) - timedelta(days=1)
                    if end > rec.to_date:
                        end = rec.to_date

                    lines.append((0,0,{'name': start.strftime("T%m/%Y"), 'from_date': start, 'to_date': end, 'currency_id': rec.currency_id.id}))
                    current = start + relativedelta(months=1)

            else:
                current = current - timedelta(days=current.weekday())

                while current <= rec.to_date:
                    start = current
                    end = start + timedelta(days=6)
                    if end > rec.to_date:
                        end = rec.to_date

                    lines.append((0,0,{'name': start.strftime("W%W/%Y"), 'from_date': start, 'to_date': end, 'currency_id': rec.currency_id.id}))
                    current = start + timedelta(days=7)

            rec.line_ids = lines

    def action_generate_sample(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError("Generate lines first")

            total = rec.total_project_amount or 0.0
            if not total:
                raise UserError("Missing total project amount")

            lines = rec.line_ids.sorted(key=lambda l: l.from_date or fields.Date.today())
            n = len(lines)
            if not n:
                return

            # S-curve đơn giản (bell shape)
            weights = [(i+1)*(n-i) for i in range(n)]
            s = sum(weights) or 1.0

            for i, l in enumerate(lines):
                pct = weights[i] * 100.0 / s
                amt = total * pct / 100.0
                l.plan_percentage = pct
                l.plan_amount = amt
                l.plan_ipc_amount = amt * 0.8

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_unlink_lines(self):
        for rec in self:
            rec.line_ids.unlink()

# tong_so_lan_goi = 0 

class DeliverablePaymentPlanLine(models.Model):
    _name = "deliverable.payment.plan.line"
    _description = "Deliverable Payment Plan Line"
    _order = "from_date"

    name = fields.Char(string="Name", compute="_compute_name", store=True)
    plan_id = fields.Many2one("deliverable.payment.plan", string="Plan", required=True, ondelete="cascade")
    currency_id = fields.Many2one(
        "res.currency",
        related="plan_id.currency_id",
        store=True,
        readonly=True
    )

    from_date = fields.Date(string="From Date", required=True)
    to_date = fields.Date(string="To Date", required=True)
    currency_id = fields.Many2one("res.currency", string="Currency", required=True, default=lambda self: self.env.company.currency_id.id)

    plan_percentage = fields.Float(string="Plan %", compute="_compute_plan", inverse="_inverse_plan", store=True)
    plan_amount = fields.Monetary(string="Plan Amount", compute="_compute_plan", inverse="_inverse_plan", store=True)
    plan_percentage_accumulated = fields.Float(string="Plan % Accumulated", compute="_compute_plan_acc", store=True)
    plan_accumulated_amount = fields.Monetary(string="Plan Accumulated Amount", compute="_compute_plan_acc", store=True)
    plan_ipc_amount = fields.Monetary(string="Plan IPC Amount")
    plan_accumulated_ipc_amount = fields.Monetary(string="Plan Accumulated IPC Amount", compute="_compute_plan_acc", store=True)

    # Nhóm 1: Sản lượng (Actual Amount & Percentage)
    actual_amount = fields.Monetary(
        string="Actual Amount", compute="_compute_actual_amount", store=True)
    actual_percentage = fields.Float(
        string="Actual %", compute="_compute_actual_amount", store=True)
    actual_accumulated_amount = fields.Monetary(
        string="Actual Accumulated Amount", compute="_compute_actual_amount", store=True)
    actual_percentage_accumulated = fields.Float(
        string="Actual % Accumulated", compute="_compute_actual_amount", store=True)

    # Nhóm 2: Nghiệm thu (IPC)
    actual_ipc_amount = fields.Monetary(
        string="Actual IPC Amount", compute="_compute_actual_ipc_amount", store=True)
    actual_accumulated_ipc_amount = fields.Monetary(
        string="Actual Accumulated IPC Amount", compute="_compute_actual_ipc_amount", store=True)

    # Nhóm 3: Thanh toán (Paid)
    actual_paid_amount = fields.Monetary(
        string="Actual Paid Amount", compute="_compute_actual_paid_amount", store=True)
    actual_accumulated_paid_amount = fields.Monetary(
        string="Actual Accumulated Paid Amount", compute="_compute_actual_paid_amount", store=True)


    @api.depends("plan_percentage","plan_amount","plan_id.total_project_amount")
    def _compute_plan(self):
        for rec in self:
            total = rec.plan_id.total_project_amount or 0.0
            if total:
                if rec.plan_percentage and not rec.plan_amount:
                    rec.plan_amount = total * rec.plan_percentage / 100
                elif rec.plan_amount and not rec.plan_percentage:
                    rec.plan_percentage = (rec.plan_amount / total) * 100

    def _inverse_plan(self):
        for rec in self:
            total = rec.plan_id.total_project_amount or 0.0
            if total:
                if rec.plan_percentage:
                    rec.plan_amount = total * rec.plan_percentage / 100
                elif rec.plan_amount:
                    rec.plan_percentage = (rec.plan_amount / total) * 100


    @api.depends(
    "plan_amount","plan_percentage","plan_ipc_amount",
    "plan_id.line_ids.plan_amount",
    "plan_id.line_ids.plan_percentage",
    "plan_id.line_ids.plan_ipc_amount"
    )
    def _compute_plan_acc(self):
        for rec in self:
            prev = rec.plan_id.line_ids.filtered(lambda l: l.from_date < rec.from_date)

            rec.plan_accumulated_amount = sum(prev.mapped("plan_amount")) + (rec.plan_amount or 0.0)
            rec.plan_percentage_accumulated = sum(prev.mapped("plan_percentage")) + (rec.plan_percentage or 0.0)
            rec.plan_accumulated_ipc_amount = sum(prev.mapped("plan_ipc_amount")) + (rec.plan_ipc_amount or 0.0)

    @api.depends("from_date")
    def _compute_name(self):
        for rec in self:
            rec.name = rec.from_date.strftime("T%m/%y") if rec.from_date else False


    # --- PHẦN PHỤ TRỢ: Lấy Contract dùng chung cho các hàm ---
    def _get_contract_info(self):
        self.ensure_one()
        plan = self.plan_id
        if plan.type == 'customer':
            return plan.customer_contract_id, 'customer'
        elif plan.type == 'subcontract':
            return plan.subcontractor_contract_id, 'subcontract'
        return False, False

    @api.depends('plan_id.type',
                 "plan_id.customer_contract_id.order_line.complete_qty",
                 "plan_id.subcontractor_contract_id.order_line.complete_qty",

                 'plan_id.customer_contract_id.order_line.qty_delivered', # Dùng trường chuẩn của Odoo hoặc Mixin
                 'plan_id.subcontractor_contract_id.order_line.qty_received',
                 )
    def _compute_actual_amount(self):
        for rec in self:
            contract, plan_type = rec._get_contract_info()
            total_amt = rec.plan_id.total_project_amount or 0.0
            actual_amount = 0.0
            
            if contract:
                for line in contract.order_line:
                    deliverables = line.task_deliverable_ids.filtered(
                        lambda x: x.status == 'approved' and 
                                  x.progress_report_id.week_start_date and
                                  rec.from_date <= x.progress_report_id.week_start_date <= rec.to_date
                    )
                    qty_in_period = sum(deliverables.mapped('completed_qty'))
                    if not qty_in_period:
                        raw_qty_in_period = line.get_delivered_in_period(rec.from_date, rec.to_date)
                        qty_in_period = line.product_id.uom_id._compute_quantity(raw_qty_in_period, line.product_uom)
                    
                    total_qty = line.product_uom_qty if plan_type == 'customer' else line.product_qty
                    if total_qty > 0:
                        actual_amount += (qty_in_period / total_qty) * line.price_total

            rec.actual_amount = actual_amount
            rec.actual_percentage = (actual_amount / total_amt * 100) if total_amt > 0 else 0.0
            
            # Tính lũy kế sản lượng
            prev_lines = rec.plan_id.line_ids.filtered(lambda l: l.from_date < rec.from_date)
            rec.actual_accumulated_amount = sum(prev_lines.mapped('actual_amount')) + actual_amount
            rec.actual_percentage_accumulated = (rec.actual_accumulated_amount / total_amt * 100) if total_amt > 0 else 0.0

    @api.depends( "plan_id.customer_contract_id.ipc_ids.total_amount",
                 "plan_id.customer_contract_id.ipc_ids.custom_status",
                 "plan_id.customer_contract_id.ipc_ids.date",
                 "plan_id.subcontractor_contract_id.ipc_ids.total_amount",
                 "plan_id.subcontractor_contract_id.ipc_ids.custom_status",
                 "plan_id.subcontractor_contract_id.ipc_ids.date")
    def _compute_actual_ipc_amount(self):
        for rec in self:
            contract, plan_type = rec._get_contract_info()
            actual_ipc_amount = 0.0
            
            ipc_domain = [
                ('date', '>=', rec.from_date),
                ('date', '<=', rec.to_date),
                ('custom_status.is_approved', '=', True)
            ]
            if plan_type == 'customer' and contract:
                ipc_domain.append(('sale_order_id', '=', contract.id))
            elif plan_type == 'subcontract' and contract:
                ipc_domain.append(('purchase_order_id', '=', contract.id))
            
            ipcs = self.env['construction.ipc'].search(ipc_domain)
            for ipc_line in ipcs.boq_line_ids:
                line = ipc_line.sale_order_line_id if plan_type == 'customer' else ipc_line.purchase_order_line_id
                if line and line.product_uom_qty > 0:
                    actual_ipc_amount += (ipc_line.quantity / line.product_uom_qty) * line.price_total
            
            rec.actual_ipc_amount = actual_ipc_amount
            
            # Tính lũy kế IPC
            prev_lines = rec.plan_id.line_ids.filtered(lambda l: l.from_date < rec.from_date)
            rec.actual_accumulated_ipc_amount = sum(prev_lines.mapped('actual_ipc_amount')) + actual_ipc_amount

    @api.depends(
                 "plan_id.customer_contract_id.invoice_ids.amount_residual",
                 "plan_id.customer_contract_id.invoice_ids.state",
                 "plan_id.subcontractor_contract_id.invoice_ids.amount_residual",
                 "plan_id.subcontractor_contract_id.invoice_ids.state",
                 )
    def _compute_actual_paid_amount(self):
        for rec in self:
            contract, _ = rec._get_contract_info()
            paid_amount = 0.0
            if contract:
                invoices = contract.invoice_ids.filtered(
                    lambda x: x.state == 'posted' and rec.from_date <= x.date <= rec.to_date
                )
                paid_amount = sum(invoices.mapped(lambda inv: inv.amount_total - inv.amount_residual))
            
            rec.actual_paid_amount = paid_amount
            
            # Tính lũy kế thanh toán
            prev_lines = rec.plan_id.line_ids.filtered(lambda l: l.from_date < rec.from_date)
            rec.actual_accumulated_paid_amount = sum(prev_lines.mapped('actual_paid_amount')) + paid_amount

    # @api.depends('plan_id.type',
    #              "plan_id.customer_contract_id.order_line.complete_qty",
    #              "plan_id.subcontractor_contract_id.order_line.complete_qty",

    #              'plan_id.customer_contract_id.order_line.qty_delivered', # Dùng trường chuẩn của Odoo hoặc Mixin
    #              'plan_id.subcontractor_contract_id.order_line.qty_received',

    #              "plan_id.customer_contract_id.ipc_ids.total_amount",
    #              "plan_id.customer_contract_id.ipc_ids.custom_status",
    #              "plan_id.customer_contract_id.ipc_ids.date",
    #              "plan_id.subcontractor_contract_id.ipc_ids.total_amount",
    #              "plan_id.subcontractor_contract_id.ipc_ids.custom_status",
    #              "plan_id.subcontractor_contract_id.ipc_ids.date",

    #              "plan_id.customer_contract_id.invoice_ids.amount_residual",
    #              "plan_id.customer_contract_id.invoice_ids.state",
    #              "plan_id.subcontractor_contract_id.invoice_ids.amount_residual",
    #              "plan_id.subcontractor_contract_id.invoice_ids.state",
 
    #              )
    # def _compute_actual(self):
    #     for rec in self:
    #         global tong_so_lan_goi
    #         tong_so_lan_goi += 1
    #         print ('**tong_so_lan_goi**', tong_so_lan_goi)
    #         from_date = rec.from_date
    #         to_date = rec.to_date
    #         total_amt = rec.plan_id.total_project_amount or 0.0
            
    #         # --- 1. KHỞI TẠO GIÁ TRỊ ---
    #         actual_amount = 0.0
    #         actual_ipc_amount = 0.0

    #         # --- 2. TÍNH SẢN LƯỢNG THỰC TẾ (ACTUAL AMOUNT) ---
    #         # Dựa trên Task Deliverables của SO hoặc PO
    #         contract = False
    #         plan_type = rec.plan_id.type
    #         if plan_type == 'customer':
    #             contract = rec.plan_id.customer_contract_id
    #         elif plan_type == 'subcontract':
    #             contract = rec.plan_id.subcontractor_contract_id

    #         if contract:
    #             for line in contract.order_line:
    #                 # Lọc các hạng mục công việc đã approved trong kỳ
    #                 deliverables = line.task_deliverable_ids.filtered(
    #                     lambda x: x.status == 'approved' and 
    #                               x.progress_report_id.week_start_date and
    #                               from_date <= x.progress_report_id.week_start_date <= to_date
    #                 )
    #                 qty_in_period = sum(deliverables.mapped('completed_qty'))
    #                 if not qty_in_period:
    #                     raw_qty_in_period = line.get_delivered_in_period(from_date, to_date)
    #                     qty_in_period = line.product_id.uom_id._compute_quantity(raw_qty_in_period, line.product_uom)
    #                 # Tránh lỗi chia cho 0
    #                 total_qty = line.product_uom_qty if plan_type == 'customer' else line.product_qty
    #                 if total_qty > 0:
    #                     actual_amount += (qty_in_period / total_qty) * line.price_total

    #         # --- 3. TÍNH NGHIỆM THU IPC THỰC TẾ (ACTUAL IPC AMOUNT) ---
    #         # Dựa trên bảng construction_ipc JOIN ipc_stage (is_approved = True)
    #         ipc_domain = [
    #             ('date', '>=', from_date),
    #             ('date', '<=', to_date),
    #             ('custom_status.is_approved', '=', True)
    #         ]
            
    #         if plan_type == 'customer' and rec.plan_id.customer_contract_id:
    #             ipc_domain.append(('sale_order_id', '=', rec.plan_id.customer_contract_id.id))
    #         elif plan_type == 'subcontract' and rec.plan_id.subcontractor_contract_id:
    #             ipc_domain.append(('purchase_order_id', '=', rec.plan_id.subcontractor_contract_id.id))
            
    #         # Tìm các bản ghi IPC thỏa điều kiện
    #         ipcs = self.env['construction.ipc'].search(ipc_domain)
            
    #         # Tính tổng từ các dòng construction_ipc_line (trường total_amount)
    #         # Dùng line_ids.total_amount để đảm bảo lấy đúng giá trị chi tiết từng dòng
    #         # actual_ipc_amount = sum(ipcs.mapped('total_amount'))
    #         actual_ipc_amount = 0.0
    #         for ipc_line in ipcs.boq_line_ids:
    #             line = ipc_line.sale_order_line_id if plan_type == 'customer' else ipc_line.purchase_order_line_id
    #             actual_ipc_amount +=  ipc_line.quantity/line.product_uom_qty*line.price_total
            
    #         # Gán giá trị thực tế trong kỳ
    #         rec.actual_amount = actual_amount
    #         rec.actual_ipc_amount = actual_ipc_amount
    #         rec.actual_paid_amount = sum(contract.invoice_ids.filtered(lambda x : x.state =='posted' and from_date <= x.date <= to_date ).mapped(lambda invoice: invoice.amount_total - invoice.amount_residual))
    #         # Tính % thực tế trong kỳ
    #         rec.actual_percentage = (actual_amount / total_amt * 100) if total_amt > 0 else 0.0

    #         # --- 4. TÍNH LŨY KẾ (ACCUMULATED) ---
    #         # Lọc các dòng trước đó trong cùng một kế hoạch (plan_id)
    #         prev_lines = rec.plan_id.line_ids.filtered(lambda l: l.from_date < rec.from_date)
            
    #         # Lũy kế = (Tổng các dòng trước) + (Dòng hiện tại)
            
    #         rec.actual_accumulated_amount = sum(prev_lines.mapped('actual_amount')) + actual_amount
    #         rec.actual_accumulated_ipc_amount = sum(prev_lines.mapped('actual_ipc_amount')) + actual_ipc_amount
    #         rec.actual_accumulated_paid_amount = sum(prev_lines.mapped('actual_paid_amount')) + rec.actual_paid_amount

    #         # % Lũy kế thực tế (Dùng để vẽ đường cong S-Curve)
    #         rec.actual_percentage_accumulated = (rec.actual_accumulated_amount / total_amt * 100) if total_amt > 0 else 0.0          
