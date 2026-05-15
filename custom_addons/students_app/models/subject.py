from odoo import models, fields


class StudentSubject(models.Model):
    _name = "student.subject"
    _description = "Subject"

    name = fields.Char(
        string="Subject Name",
        required=True
    )

    code = fields.Char(
        string="Subject Code",
        required=True
    )

    semester = fields.Integer(
        string="Semester",
        required=True
    )

    department_ids = fields.Many2many(
        'student.department',
        'student_subject_department_rel',   # relation table
        'subject_id',                       # this model column
        'department_id',                    # other model column
        string="Departments"
    )

    _sql_constraints = [
        ('unique_name_semester',
         'unique(name, semester)',
         'Subject already exists in this semester!')
    ]