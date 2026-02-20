from odoo import models, fields, api

class StudentSkills(models.Model):
    _name = 'student.skills'
    _description = 'Student Skills'

    name = fields.Char(string="Skill Name", required=True)
