from odoo import models, fields


class StudentExam(models.Model):
    _name = "student.exam"
    _description = "Exam"

    department_id = fields.Many2one(
        'student.department',
        string="Department",
        required=True
    )

    exam_date = fields.Date(
        string="Exam Date",
        required=True
    )

    semester = fields.Integer(
        string="Semester"
    )

    # Exam Category
    category = fields.Selection(
        [
            ('cycle1', 'Cycle Test 1'),
            ('cycle2', 'Cycle Test 2'),
            ('semester', 'Semester Exam')
        ],
        string="Exam Category",
        required=True
    )

    subject_ids = fields.Many2many(
        'student.subject',
        string="Subjects"
    )
