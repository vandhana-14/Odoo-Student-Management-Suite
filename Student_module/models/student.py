from odoo import models, fields ,api
from datetime import datetime

class Student(models.Model):
    _name = 'student.student'
    _description = 'Student'

    name = fields.Char(string="Name",required=True)
    student_code = fields.Char(string="Student Code",readonly=True, copy=False) 
    dob = fields.Date(string="Date of Birth",required=True)
    age = fields.Integer(string="Age",compute="_compute_age",store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],required=True)
    department_id = fields.Many2one('student.department',string="Department", required=True)
    skills = fields.Many2many('student.skills', string="Skills")
    joining_date = fields.Date(string="Joining Date",required=True)
    mobile = fields.Char(string="Mobile",required=True,unique=True)
    email = fields.Char(string="Email",required=True,unique=True)
    address = fields.Text(string="Address",required=True)
    location = fields.Char(string="Location",required=True)
    active = fields.Boolean(default=True,)
    image=fields.Binary(string="Image")
    
    _sql_constraints = [
    ('student_code_unique', 'unique(student_code)', 'Student ID must be unique!')
    ]

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
    
    #Delete Button

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

        return super().create(vals_list)
    
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
    


    