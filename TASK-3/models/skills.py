from odoo import models, fields, api

class StudentSkills(models.Model):
    _name = "student.skills"
    _description = "Student Skills"

    name = fields.Char(required=True)
    color = fields.Integer("Color")

    # AUTO COLOR (SEQUENTIAL)
    @api.model
    def create(self, vals):
        if not vals.get('color'):
            last = self.search([], order="id desc", limit=1)
            vals['color'] = ((last.color + 1) % 11) + 1 if last else 1
        return super().create(vals)