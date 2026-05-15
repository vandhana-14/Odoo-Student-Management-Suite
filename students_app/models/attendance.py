from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import pytz


class StudentAttendance(models.Model):
    _name = "student.attendance"
    _description = "Student Attendance"

    _unique_student_date = models.Constraint(
        'unique(student_id, date)',
        'Attendance already exists for this student today!',
    )

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

    date = fields.Date(
        default=fields.Date.today,
        required=True
    )

    check_in_time = fields.Datetime(string="Check In Time")
    check_out_time = fields.Datetime(string="Check Out Time")

    late_time = fields.Char(
        string="Late Time",
        compute="_compute_late_arrival",
        store=True
    )

    total_hours = fields.Float(
        string="Total Hours",
        compute="_compute_total_hours",
        store=True
    )

    # =====================================================
    # CONSTRAINT — clean error instead of raw DB error
    # =====================================================
    @api.constrains('student_id', 'date')
    def _check_unique_attendance(self):
        for rec in self:
            duplicate = self.search([
                ('student_id', '=', rec.student_id.id),
                ('date', '=', rec.date),
                ('id', '!=', rec.id)
            ])
            if duplicate:
                raise ValidationError(
                    "Attendance already exists for this student today!"
                )

    # =====================================================
    # AUTO DISPLAY EXISTING ATTENDANCE WHEN SELECTING STUDENT
    # =====================================================
    @api.onchange('student_id')
    def _onchange_student_auto_time(self):
        if not self.student_id:
            return

        today = fields.Date.today()

        # FIX: use self._origin.id to correctly exclude the current record
        # in all cases — new form, saved form, and after submit redirect
        exclude_id = self._origin.id if self._origin else (self.id.origin if self.id else 0)

        existing = self.search([
            ('student_id', '=', self.student_id.id),
            ('date', '=', today),
            ('id', '!=', exclude_id)
        ], limit=1)

        # Only show existing attendance from another record
        if existing:
            self.check_in_time = existing.check_in_time
            self.check_out_time = existing.check_out_time
        else:
            self.check_in_time = False
            self.check_out_time = False

    # =====================================================
    # BUTTON LOGIC
    # =====================================================
    def action_submit_attendance(self):
        self.ensure_one()

        if not self.student_id:
            raise ValidationError("Please select student.")

        today = fields.Date.today()
        now = fields.Datetime.now()

        # If this record already saved in DB
        if self.id:

            # First time check-in
            if not self.check_in_time:
                self.write({
                    'check_in_time': now
                })
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'student.attendance',
                    'view_mode': 'list,calendar,graph',
                    'target': 'current'
                }

            # Checkout
            if self.check_in_time and not self.check_out_time:
                self.write({
                    'check_out_time': now
                })
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'student.attendance',
                    'view_mode': 'list,calendar,graph',
                    'target': 'current'
                }

            # Already done
            if self.check_out_time:
                raise ValidationError("Already checked out today.")

        # If record not yet saved → check for existing first, then create
        else:
            # Pre-check before create to give a clean ValidationError
            existing = self.search([
                ('student_id', '=', self.student_id.id),
                ('date', '=', today)
            ], limit=1)

            if existing:
                raise ValidationError(
                    "Attendance already exists for this student today."
                )

            self.create({
                'student_id': self.student_id.id,
                'date': today,
                'check_in_time': now
            })

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'student.attendance',
                'view_mode': 'list,calendar,graph',
                'target': 'current'
            }

    # =====================================================
    # LATE CALCULATION
    # =====================================================
    @api.depends('check_in_time')
    def _compute_late_arrival(self):
        for rec in self:
            if not rec.check_in_time:
                rec.late_time = "00:00:00"
                continue

            # Explicitly resolve timezone from user context, fallback to UTC
            tz_name = rec.env.context.get('tz') or rec.env.user.tz or 'UTC'
            user_tz = pytz.timezone(tz_name)

            # Convert UTC datetime stored in DB → user's local time
            check_in_local = rec.check_in_time.replace(tzinfo=pytz.utc).astimezone(user_tz)

            # Build 9:15 AM limit on the same local date
            limit_time = datetime(
                check_in_local.year,
                check_in_local.month,
                check_in_local.day,
                9, 15, 0
            )

            check_in_naive = check_in_local.replace(tzinfo=None)

            diff_seconds = int((check_in_naive - limit_time).total_seconds())

            if diff_seconds > 0:
                hours = diff_seconds // 3600
                minutes = (diff_seconds % 3600) // 60
                seconds = diff_seconds % 60
                rec.late_time = f"{hours:02}:{minutes:02}:{seconds:02}"
            else:
                rec.late_time = "00:00:00"

    # =====================================================
    # TOTAL HOURS
    # =====================================================
    @api.depends('check_in_time', 'check_out_time')
    def _compute_total_hours(self):
        for rec in self:
            if rec.check_in_time and rec.check_out_time:
                diff = rec.check_out_time - rec.check_in_time
                rec.total_hours = diff.total_seconds() / 3600.0
            else:
                rec.total_hours = 0
