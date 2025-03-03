from odoo import models, fields

class HealthcareFeedback(models.Model):
    _name = 'healthcare.feedback'
    _description = 'Phản hồi của bệnh nhân'

    patient_id = fields.Many2one('healthcare.patient', string="Bệnh nhân", required=True)
    feedback = fields.Text(string="Nội dung phản hồi", required=True)
    date = fields.Date(string="Ngày phản hồi", default=fields.Date.context_today)
    rating = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ], string="Đánh giá")
