from odoo import models, fields, api
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

    # Label	Field	Type	Required	Help?
    # Name	name	Char	Yes	Kế hoạch sản lượng thanh toán ...
    # Description	description	Text	No	
    # Type	type	"Selection
    # + Customer Contract
    # + Subcontractor Contract
    # Default: null"	Yes	
    # From Date	from_date	From Date	Yes	
    # To Date	to_date	To Date	Yes	
    # Customer Contract	customer_contract_id	"many2one: sale.order
    # filter domain: is_customer_contract = True"	Chỉ Required khi type = Customer Contract	Chỉ hiển thị khi type = Customer Contract
    # Subcontractor Contract	subcontractor_contract_id	"many2one: purchase.order
    # filter domain: is_sub_contract = True"	Chỉ Required khi type = Subcontractor Contract	Chỉ hiển thị khi type = Subcontractor Contract
    # Currency	currency_id	Many2one	Default lấy theo currency của cty	
    # Project	project_id	"many2one: project.project
    # filter domain: các dự án có hợp đồng"	Yes	
    # Plan lines	line_ids	one2many		
    # State	state	"Selection
    # + Draft
    # + Confirm"		

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
    time_range_type = fields.Selection([
        ('month', 'Month'),
        ('week', 'Week')
    ], default='month', required=True)

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

            if rec.time_range_type == 'month':
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

    # Label	Field	Type	Required	Description
    # Name	name	Char	Yes	"Readonly. Hệ thống tự Compute theo thời gian from_date, to_date
    # Format Tháng: T01/26
    # Format Tuần: W01/26
    # Hệ thống tự tính theo format trên"
    # Từ Ngày	from_date	Date	Yes	"Readonly
    # Ngày thứ 2 đầu tuần, hoặc ngày 01 đầu tháng"
    # Đến Ngày	to_date	Date	Yes	"Readonly
    # Ngày cuối tuần, hoặc ngày cuối tháng"
    # Tỷ lệ % SL	plan_percentage	Float		
    # Giá trị SL	plan_amount	Monetary		
    # % Lũy kế SL	plan_percentage_accumulated	Float		
    # Giá trị lũy kế SL	plan_accumulated_amount	Monetary		
    # Giá trị nghiệm thu IPC	plan_ipc_amount	Monetary		
    # Giá trị nghiệm thu IPC	plan_accumulated_ipc_amount	Monetary		
                    
    # Tỷ lệ % SL thực tế	actual_percentage	Float		Hệ thống tính
    # Giá trị SL	actual_amount	Monetary		Hệ thống tính
    # % Lũy kế SL	actual_percentage_accumulated	Float		Hệ thống tính
    # Giá trị lũy kế SL	actual_accumulated_amount	Monetary		Hệ thống tính
    # Giá trị thanh toán	actual_paid_amount	Monetary		Hệ thống tính
    # Giá trị nghiệm thu IPC	actual_ipc_amount	Monetary		Tổng giá trị IPC ở trạng thái hoàn thành
    # Lũy kế nghiệm thu IPC	actual_accumulated_ipc_amount	Monetary		Lũy kế giá trị IPC ở trạng thái hoàn thành
    # Lũy kế thanh toán	actual_accumulated_pai_amount	Monetary		Hệ thống tính


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

    plan_percentage = fields.Float(string="Plan %", compute="_compute_plan", inverse="_inverse_plan", store=True)
    plan_amount = fields.Monetary(string="Plan Amount", compute="_compute_plan", inverse="_inverse_plan", store=True)
    plan_percentage_accumulated = fields.Float(string="Plan % Accumulated", compute="_compute_plan_acc", store=True)
    plan_accumulated_amount = fields.Monetary(string="Plan Accumulated Amount", compute="_compute_plan_acc", store=True)
    plan_ipc_amount = fields.Monetary(string="Plan IPC Amount")
    plan_accumulated_ipc_amount = fields.Monetary(string="Plan Accumulated IPC Amount", compute="_compute_plan_acc", store=True)

    actual_percentage = fields.Float(string="Actual %", compute="_compute_actual", store=True)
    actual_amount = fields.Monetary(string="Actual Amount", compute="_compute_actual", store=True)
    actual_percentage_accumulated = fields.Float(string="Actual % Accumulated", compute="_compute_actual", store=True)
    actual_accumulated_amount = fields.Monetary(string="Actual Accumulated Amount", compute="_compute_actual", store=True)
    actual_paid_amount = fields.Monetary(string="Actual Paid Amount", compute="_compute_actual", store=True)
    actual_ipc_amount = fields.Monetary(string="Actual IPC Amount", compute="_compute_actual", store=True)
    actual_accumulated_ipc_amount = fields.Monetary(string="Actual Accumulated IPC Amount", compute="_compute_actual", store=True)
    actual_accumulated_paid_amount = fields.Monetary(string="Actual Accumulated Paid Amount", compute="_compute_actual", store=True)

    currency_id = fields.Many2one("res.currency", string="Currency", required=True, default=lambda self: self.env.company.currency_id.id)

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
    
    @api.depends("plan_amount", "plan_percentage", "plan_id.line_ids.actual_amount", "plan_id.line_ids.actual_percentage")
    def _compute_actual(self):
        return 
        for rec in self:
            prev_lines = rec.plan_id.line_ids.filtered(lambda l: l.from_date < rec.from_date)
            rec.actual_amount = rec.plan_amount * 0.9 if rec.plan_amount else 0.0
            rec.actual_percentage = rec.plan_percentage * 0.9 if rec.plan_percentage else 0.0
            rec.actual_accumulated_amount = sum(prev_lines.mapped("actual_amount")) + rec.actual_amount
            rec.actual_percentage_accumulated = sum(prev_lines.mapped("actual_percentage")) + rec.actual_percentage
            rec.actual_ipc_amount = rec.actual_amount * 0.8
            rec.actual_accumulated_ipc_amount = sum(prev_lines.mapped("actual_ipc_amount")) + rec.actual_ipc_amount
            rec.actual_paid_amount = rec.actual_amount * 0.7
            rec.actual_accumulated_paid_amount = sum(prev_lines.mapped("actual_paid_amount")) + rec.actual_paid_amount