from odoo import models, fields, api


class StudentScoreRecord(models.Model):
    _name = "student.score.record"
    _description = "Student Score Record"

    student_id = fields.Many2one(
        "student.student",
        string="Student ID",
        required=True
    )
    student_name = fields.Char(
        string="Student Name",
        related="student_id.name",
        store=False,
        readonly=True
    )
    department_id = fields.Many2one(
        "student.department",
        string="Department",
        related="student_id.department_id",
        store=False,
        readonly=True
    )
    category = fields.Selection(
        [
            ('cycle1', 'Cycle Test 1'),
            ('cycle2', 'Cycle Test 2'),
            ('semester', 'Semester Exam')
        ],
        string="Exam Category",
        required=True
    )
    semester = fields.Selection(
        [
            ('1', 'Semester 1'),
            ('2', 'Semester 2'),
            ('3', 'Semester 3'),
            ('4', 'Semester 4'),
            ('5', 'Semester 5'),
            ('6', 'Semester 6'),
            ('7', 'Semester 7'),
            ('8', 'Semester 8'),
        ],
        string="Semester",
        required=True
    )
    line_ids = fields.One2many(
        "student.score.record.line",
        "score_record_id",
        string="Exam Results",
        readonly=True
    )

    @api.onchange("student_id", "category", "semester")
    def _onchange_filters(self):
        for rec in self:
            rec._load_result_lines()

    def action_fetch_results(self):
        for rec in self:
            rec._load_result_lines()
        return True

    def _load_result_lines(self):
        self.ensure_one()
        self.line_ids = [(5, 0, 0)]

        if not self.student_id or not self.category or not self.semester:
            return

        semester_value = int(self.semester) if self.semester else False

        marks = self.env["student.marks"].search(
            [
                ("student_id", "=", self.student_id.id),
                ("semester", "=", semester_value),
                ("exam_category", "=", self.category),
            ],
            order="id desc",
            limit=1,
        )
        if not marks:
            return

        exam = self.env["student.exam"].search(
            [
                ("department_id", "=", self.student_id.department_id.id),
                ("category", "=", self.category),
            ],
            order="exam_date desc, id desc",
            limit=1,
        )

        exam_date = exam.exam_date if exam else False
        lines = []
        for mark_line in marks.mark_line_ids:
            subject = mark_line.subject_id
            lines.append(
                (
                    0,
                    0,
                    {
                        "course_id": subject.code or str(subject.id),
                        "course_name": subject.name or "",
                        "exam_date": exam_date,
                        "total_mark": mark_line.max_marks,
                        "obtained_mark": mark_line.obtained_marks,
                        "grade": mark_line.grade,
                    },
                )
            )

        self.line_ids = lines


class StudentScoreRecordLine(models.Model):
    _name = "student.score.record.line"
    _description = "Student Score Record Line"

    score_record_id = fields.Many2one(
        "student.score.record",
        string="Score Record",
        required=True,
        ondelete="cascade",
    )
    course_id = fields.Char(string="Course ID", readonly=True)
    course_name = fields.Char(string="Course Name", readonly=True)
    exam_date = fields.Date(string="Exam Date", readonly=True)
    total_mark = fields.Float(string="Total Mark", readonly=True)
    obtained_mark = fields.Float(string="Obtained Mark", readonly=True)
    grade = fields.Char(string="Grade", readonly=True)
