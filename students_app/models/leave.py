from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class StudentLeave(models.Model):
    _name = "student.leave"
    _description = "Leave"

    _sql_constraints = [
        ('unique_student_date',
         'unique(student_id, date_from)',
         'Leave already created today!')
    ]

    student_id = fields.Many2one(
        'student.student',
        string="Student",
        required=True
    )

    # Fetch student image
    image = fields.Binary(
        string="Photo",
        related="student_id.image",
        store=False
    )

    # Fetch student name
    student_name = fields.Char(
        string="Student Name",
        related="student_id.name",
        store=False
    )

    # Fetch department
    department_id = fields.Many2one(
        'student.department',
        string="Department",
        related="student_id.department_id",
        store=False
    )

    leave_type = fields.Selection(
        [
            ('sick', 'Sick'),
            ('casual', 'Casual'),
            ('emergency', 'Emergency'),
        ],
        string="Leave Type",
        required=True
    )

    date_from = fields.Date(
        string="From Date",
        required=True
    )

    date_to = fields.Date(
        string="To Date",
        required=True
    )

    reason = fields.Text(
        string="Reason"
    )

    days = fields.Float(
        string="Number of Days",
        compute="_compute_leave_days",
        store=True
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string="State",
        default="draft"
    )

    approved_by = fields.Many2one(
        'res.users',
        string="Approved By",
    )

    # Date Validation
    @api.constrains('date_from', 'date_to')
    def _check_leave_dates(self):
        for rec in self:
            today = date.today()

            # From date cannot be in the past
            if rec.date_from and rec.date_from < today:
                raise ValidationError(
                    "From Date cannot be in the past."
                )

            # To date cannot be before From date
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(
                    "To Date cannot be earlier than From Date."
                )

    # Constraint: Only one leave per day
    @api.constrains('student_id', 'date_from')
    def _check_one_leave_per_day(self):
        for rec in self:
            if rec.student_id and rec.date_from:
                leave = self.search([
                    ('student_id', '=', rec.student_id.id),
                    ('date_from', '=', rec.date_from),
                    ('id', '!=', rec.id)
                ])
                if leave:
                    raise ValidationError(
                        "A student can apply only one leave per day."
                    )

    # Compute total leave days
    @api.depends('date_from', 'date_to')
    def _compute_leave_days(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.days = (rec.date_to - rec.date_from).days + 1
            else:
                rec.days = 0

    def action_submit(self):
        for rec in self:
            rec.state = 'draft'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            rec.approved_by = self.env.user.id

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
            rec.approved_by = self.env.user.id