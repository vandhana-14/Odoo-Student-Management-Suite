{
    'name': 'Students Management',
    'author':'THANUSH PRIYAN',
    'description': 'A module to manage students information',
    'category': 'Education',
    'version': '19.0.1',
    'sequence': 1,
    'license': 'LGPL-3',
    'depends': ['base', 'spreadsheet_dashboard'],
    'application': True,

    'data': [
        'security/groups.xml',          
        'security/ir.model.access.csv', 
        'security/record_rules.xml',
        'views/dashboard.xml',

        'views/bulk_password_reset_view.xml',
        'views/student_leave_views.xml',
        'views/student_views.xml',
        'views/student_entry.xml',
        'views/edit_form.xml',
        'views/attendance_view.xml',
        'views/attendance_form.xml',
        'views/student_mark_view.xml',
        'views/action.xml',
        'views/menu.xml',
        'views/course_exam_entry_view.xml',
        'views/student/student_score.xml',
        
    ],

    'assets': {
        'web.assets_backend': [
            'students_app/static/src/css/kanban_view.css',

        ],
    },
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
}
