from odoo import models, fields, api


class StudentMarksLine(models.Model):
    _name = "student.marks.line"
    _description = "Student Marks Line"

    marks_id = fields.Many2one(
        'student.marks',
        string="Marks",
        required=True,
        ondelete="cascade"
    )

    subject_id = fields.Many2one(
        'student.subject',
        string="Subject",
        required=True
    )

    max_marks = fields.Float(
        string="Maximum Marks",
        default=100
    )

    obtained_marks = fields.Float(
        string="Obtained Marks",
        default=0.0
    )

    grade = fields.Char(
        string="Grade",
        compute="_compute_grade",
        store=True
    )

    result = fields.Selection(
        [
            ('pass', 'Pass'),
            ('fail', 'Fail')
        ],
        string="Result",
        compute="_compute_grade",
        store=True
    )

    @api.depends('obtained_marks', 'max_marks')
    def _compute_grade(self):
        for rec in self:

            if rec.max_marks and rec.obtained_marks is not None:

                percentage = (rec.obtained_marks / rec.max_marks) * 100

                if percentage >= 90:
                    rec.grade = 'A'
                elif percentage >= 75:
                    rec.grade = 'B'
                elif percentage >= 60:
                    rec.grade = 'C'
                elif percentage >= 50:
                    rec.grade = 'D'
                else:
                    rec.grade = 'F'

                rec.result = 'pass' if percentage >= 50 else 'fail'

            else:
                rec.grade = False
                rec.result = False


