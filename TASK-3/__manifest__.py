{
    'name': 'Students Management',
    'author':'THANUSH PRIYAN',
    'description': 'A module to manage students information',
    'category': 'Education',
    'version': '1.0.1',
    'depends': ['base'],
    'application': True,

    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/student_views.xml',
        'views/student_entry.xml',
        'views/edit_form.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'students_app/static/src/css/kanban_view.css',

        ],
    },
}
