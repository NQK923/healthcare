from odoo import models, fields, api

class HealthcarePatient(models.Model):
    _name = 'healthcare.patient'
    _description = 'Thông tin bệnh nhân'

    name = fields.Char(string="Họ và tên", required=True)
    email = fields.Char(string="Email")
    phone = fields.Char(string="Số điện thoại")
    address = fields.Char(string="Địa chỉ")
    date_of_birth = fields.Date(string="Ngày sinh")
    appointments_ids = fields.One2many('healthcare.appointment', 'patient_id', string="Lịch hẹn")
    feedback_ids = fields.One2many('healthcare.feedback', 'patient_id', string="Phản hồi")
    complaint_ids = fields.One2many('healthcare.complaint', 'patient_id', string="Khiếu nại")
