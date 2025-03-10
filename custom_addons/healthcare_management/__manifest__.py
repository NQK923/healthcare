{
    'name': "Healthcare Management",
    'version': '1.0',
    'summary': "Quản lý liên lạc và chăm sóc khách hàng cho bệnh nhân",
    'description': """
        Module giúp quản lý lịch hẹn, gửi thông báo, email, SMS và quản lý phản hồi, khiếu nại từ bệnh nhân.
    """,
    'author': "Tên của bạn",
    'website': "http://example.com",
    'category': 'Healthcare',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'data/scheduler_data.xml',
        'data/feedback_sequence.xml',
        'views/patient_views.xml',
        'views/appointment_views.xml',
        'views/feedback_views.xml',
        'views/complaint_views.xml',
    ],
    'installable': True,
    'application': True,
}
