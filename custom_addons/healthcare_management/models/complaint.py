from odoo import models, fields

class HealthcareComplaint(models.Model):
    _name = 'healthcare.complaint'
    _description = 'Khiếu nại từ bệnh nhân'

    patient_id = fields.Many2one('healthcare.patient', string="Bệnh nhân", required=True)
    complaint = fields.Text(string="Nội dung khiếu nại", required=True)
    date = fields.Date(string="Ngày khiếu nại", default=fields.Date.context_today)
    state = fields.Selection([
        ('new', 'Mới'),
        ('in_progress', 'Đang xử lý'),
        ('resolved', 'Đã giải quyết')
    ], default='new', string="Trạng thái")
