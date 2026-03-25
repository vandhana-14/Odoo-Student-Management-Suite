from odoo import models, fields, api


class BulkPasswordReset(models.TransientModel):
    _name = 'student.bulk.password.reset'
    _description = 'Bulk Password Reset'

    student_ids = fields.Many2many(
        'student.student',
        string="Students"
    )

    new_password = fields.Char(
        string="New Password",
        required=True
    )

    def action_reset_password(self):

        for student in self.student_ids:

            if student.user_id:
                user = student.user_id.sudo()

                # Hash password using Odoo's crypt context
                encrypted = user._crypt_context().hash(self.new_password)

                # Write directly to DB to bypass session invalidation
                self.env.cr.execute(
                    "UPDATE res_users SET password = %s WHERE id = %s",
                    (encrypted, user.id)
                )

                # Clear the ORM cache for this field
                user.invalidate_recordset(['password'])

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Passwords reset successfully!',
                'type': 'success',
            }
        }