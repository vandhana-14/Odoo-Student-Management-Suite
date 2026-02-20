from odoo import models, fields ,api

class Student(models.Model):
    _name = 'student.student'
    _description = 'Student'

    name = fields.Char(string="Name",required=True)
    student_code = fields.Char(string="Student Code",required=True)
    dob = fields.Date(string="Date of Birth",required=True)
    age = fields.Integer(string="Age",compute="_compute_age",store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],required=True)
    department_id = fields.Many2one('student.department',string="Department",required=True)
    skills = fields.Many2many('student.skills', string="Skills")
    joining_date = fields.Date(string="Joining Date",required=True)
    mobile = fields.Char(string="Mobile",required=True)
    email = fields.Char(string="Email")
    address = fields.Text(string="Address")
    location = fields.Char(string="Location")
    active = fields.Boolean(default=True,)
    image=fields.Binary(string="Image")


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
    def action_delete(self):
        self.unlink()

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