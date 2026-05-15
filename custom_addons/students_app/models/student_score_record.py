from odoo import models, fields, api

class StudentScoreRecord(models.Model):
    _name = "student.score.record"
    _description = "Student Score Record"

    subject_code = fields.Char("Subject Code")
    subject_name = fields.Char("Subject Name")
    exam_year = fields.Integer("Exam Year")
    exam_month = fields.Integer("Exam Month")
    grade = fields.Char("Grade")
    credits = fields.Float("Credits")

    semester = fields.Selection([
        ('1','Semester 1'),
        ('2','Semester 2'),
        ('3','Semester 3'),
        ('4','Semester 4'),
        ('5','Semester 5'),
        ('6','Semester 6'),
        ('7','Semester 7'),
        ('8','Semester 8')
    ], string="Semester")

    category = fields.Selection([
        ('cycle1','Cycle Test 1'),
        ('cycle2','Cycle Test 2'),
        ('semester','Semester Exam')
    ], string="Category")

    student_code = fields.Char("Student Code")

    @api.model
    def get_student_marks(self, semester, category):
        """
        Fetch marks using Odoo ORM
        """
        student_login = self.env.user.login

        # Find the student record associated with the current user login
        student = self.env['student.student'].search([('email', '=', student_login)], limit=1)
        if not student:
            return []

        # Find marks for this student
        marks = self.env['student.marks'].search([
            ('student_id', '=', student.id),
            ('semester', '=', int(semester)),
            ('exam_category', '=', category)
        ])

        result = []
        for mark in marks:
            for line in mark.mark_line_ids:
                result.append({
                    'subject_code': line.subject_id.code,
                    'subject_name': line.subject_id.name,
                    'exam_year': mark.create_date.year,
                    'exam_month': mark.create_date.month,
                    'grade': line.grade,
                    'credits': line.subject_id.credits
                })
        return result