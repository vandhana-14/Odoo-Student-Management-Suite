from odoo import models, fields, api


class StudentMarks(models.Model):
    _name = "student.marks"
    _description = "Student Marks"

    student_id = fields.Many2one(
        'student.student',
        string="Student ID",
        required=True
    )

    student_name = fields.Char(
        string="Student Name",
        related="student_id.name",
        store=False
    )

    department_id = fields.Many2one(
        'student.department',
        string="Department",
        related="student_id.department_id",
        store=False
    )

    semester = fields.Integer(
        string="Semester",
        required=True
    )

    exam_category = fields.Selection(
        [
            ('cycle1', 'Cycle Test 1'),
            ('cycle2', 'Cycle Test 2'),
            ('semester', 'Semester Exam')
        ],
        string="Exam Category",
        required=True
    )

    mark_line_ids = fields.One2many(
        'student.marks.line',
        'marks_id',
        string="Subject Marks"
    )

    total_subjects = fields.Integer(
        string="Total Subjects",
        compute="_compute_totals",
        store=True
    )

    total_marks = fields.Float(
        string="Total Marks",
        compute="_compute_totals",
        store=True
    )

    total_grade = fields.Char(
        string="Total Grade",
        compute="_compute_totals",
        store=True
    )

    # -----------------------------
    # AUTO LOAD SUBJECTS BY SEMESTER
    # -----------------------------
    @api.onchange('student_id','semester','exam_category')
    def _onchange_load_subjects(self):

        if not self.student_id or not self.semester:
            return

        department = self.student_id.department_id

        subjects = self.env['student.subject'].search([
            ('semester', '=', self.semester),
            ('department_ids', 'in', department.id)
        ])

        lines = []
        for subject in subjects:
            lines.append((0,0,{
                'subject_id': subject.id,
                'max_marks':100
            }))

        self.mark_line_ids = [(5,0,0)] + lines

    # -----------------------------
    # TOTAL MARK CALCULATION
    # -----------------------------
    @api.depends('mark_line_ids.obtained_marks')
    def _compute_totals(self):
        for rec in self:
            total = sum(rec.mark_line_ids.mapped('obtained_marks'))
            count = len(rec.mark_line_ids)

            rec.total_subjects = count
            rec.total_marks = total

            percentage = (total / (count * 100)) * 100 if count else 0

            if percentage >= 90:
                rec.total_grade = 'A'
            elif percentage >= 75:
                rec.total_grade = 'B'
            elif percentage >= 60:
                rec.total_grade = 'C'
            elif percentage >= 50:
                rec.total_grade = 'D'
            else:
                rec.total_grade = 'F'