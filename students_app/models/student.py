from odoo import models, fields, api
from datetime import datetime


class Student(models.Model):
    _name = 'student.student'
    _description = 'Student'
    _rec_name = 'student_code'

    role = fields.Selection([
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('student', 'Student')
    ], string="Role", default='student', required=True)

    name = fields.Char(string="Name", required=True)
    student_code = fields.Char(string="Student Code", readonly=True, copy=False)
    dob = fields.Date(string="Date of Birth", required=True)
    age = fields.Integer(string="Age", compute="_compute_age", store=True)

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], required=True)

    department_id = fields.Many2one(
        'student.department',
        string="Department",
        required=True
    )

    skills = fields.Many2many('student.skills', string="Skills")
    # Aliases expected by ask_ai (no logic change)
    date_of_birth = fields.Date(related="dob", store=True, string="Date of Birth (Alias)")
    enrollment_date = fields.Date(related="joining_date", store=True, string="Joining Date (Alias)")
    skills_ids = fields.Many2many(related="skills", string="Skills (Alias)", store=False)

    joining_date = fields.Date(string="Joining Date", required=True)

    mobile = fields.Char(string="Mobile", required=True)
    email = fields.Char(string="Email", required=True)

    address = fields.Text(string="Address", required=True)
    location = fields.Char(string="Location", required=True)

    active = fields.Boolean(default=True)
    image = fields.Binary(string="Image")

    user_id = fields.Many2one(
        'res.users',
        string="Related User"
    )

    _unique_student_code = models.Constraint(
        'unique(student_code)',
        'Student ID must be unique!',
    )
    _unique_mobile = models.Constraint(
        'unique(mobile)',
        'Mobile number must be unique!',
    )
    _unique_email = models.Constraint(
        'unique(email)',
        'Email must be unique!',
    )

    # UPDATE BUTTON
    def action_update(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Update Success',
                'message': 'Student Updated Successfully!',
                'type': 'success',
                'next': self.env.ref('students_app.action_student').id,
            }
        }

    # DELETE BUTTON
    def action_delete(self):
        self.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Delete Success',
                'message': 'Student Deleted Successfully!',
                'type': 'success',
                'next': self.env.ref('students_app.action_student').id,
            }
        }

    # SUBMIT BUTTON
    def action_submit(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Student Added Successfully!',
                'type': 'success',
                'next': self.env.ref('students_app.action_student').id,
            }
        }

    # RESET BUTTON
    def action_reset(self):
        for rec in self:
            rec.name = False
            rec.student_code = False
            rec.age = 0
            rec.mobile = False
            rec.email = False
        return True

    # AGE AUTO CALCULATION
    @api.depends('dob')
    def _compute_age(self):
        for rec in self:
            if rec.dob:
                today = fields.Date.today()
                rec.age = today.year - rec.dob.year - (
                    (today.month, today.day) < (rec.dob.month, rec.dob.day)
                )
            else:
                rec.age = 0

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if not vals.get('student_code') and vals.get('department_id'):

                dept = self.env['student.department'].browse(vals['department_id'])

                year = datetime.now().strftime("%y")
                dept_code = dept.code or "GEN"

                last_student = self.search([
                    ('department_id', '=', dept.id),
                    ('student_code', 'like', f"ST{year}{dept_code}%")
                ], order="student_code desc", limit=1)

                if last_student and last_student.student_code:
                    last_num = int(last_student.student_code[-3:])
                    new_num = last_num + 1
                else:
                    new_num = 1

                vals['student_code'] = f"ST{year}{dept_code}{str(new_num).zfill(3)}"

        records = super().create(vals_list)

        # CREATE LOGIN USER WITH DEFAULT PASSWORD
        for rec in records:
            if rec.email:

                existing_user = self.env['res.users'].sudo().search(
                    [('login', '=', rec.email)], limit=1)

                if not existing_user:

                    if rec.role == 'admin':
                        group = self.env.ref('students_app.group_student_admin')
                    elif rec.role == 'staff':
                        group = self.env.ref('students_app.group_student_staff')
                    else:
                        group = self.env.ref('students_app.group_student_user')

                    # Ensure partner required fields default during user creation
                    # Create partner explicitly to satisfy NOT NULL fields (e.g., autopost_bills)
                    partner = self.env['res.partner'].sudo().create({
                        'name': rec.name,
                        'email': rec.email,
                        'type': 'contact',
                        'autopost_bills': False,
                    })

                    user = self.env['res.users'].sudo().create({
                        'name': rec.name,
                        'login': rec.email,
                        'email': rec.email,
                        'partner_id': partner.id,
                        'group_ids': [(6, 0, [group.id])],
                        'company_id': self.env.company.id
                    })

                    user.sudo().write({'password': 'password123'})

                    rec.user_id = user.id

        return records

    @api.onchange('department_id')
    def _onchange_department(self):

        if self.department_id:

            year = datetime.now().strftime("%y")
            dept_code = self.department_id.code or "GEN"

            last_student = self.env['student.student'].search([
                ('department_id', '=', self.department_id.id),
                ('student_code', 'like', f"ST{year}{dept_code}%")
            ], order="student_code desc", limit=1)

            if last_student and last_student.student_code:
                last_num = int(last_student.student_code[-3:])
                new_num = last_num + 1
            else:
                new_num = 1

            self.student_code = f"ST{year}{dept_code}{str(new_num).zfill(3)}"

    @api.model
    def default_get(self, fields_list):

        res = super().default_get(fields_list)

        if self.env.user.has_group('students_app.group_student_staff'):
            res['role'] = 'student'

        return res
