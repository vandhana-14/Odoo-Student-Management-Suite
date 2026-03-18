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
        Fetch marks only for logged-in student
        """
        student_code = self.env.user.login

        query = """
            SELECT 
                subject_code,
                subject_name,
                exam_year,
                exam_month,
                grade,
                credits
            FROM student_marks_table
            WHERE student_code = %s
            AND semester = %s
            AND category = %s
        """

        self.env.cr.execute(query, (student_code, semester, category))
        return self.env.cr.dictfetchall()