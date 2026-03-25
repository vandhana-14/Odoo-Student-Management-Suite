from odoo import models, fields

class StudentDepartment(models.Model):
    _name = "student.department"
    _description = "Department"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    

    _unique_name = models.Constraint(
        'unique(name)',
        'Department must be unique!',
    )
    
