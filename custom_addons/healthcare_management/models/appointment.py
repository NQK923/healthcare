from odoo import models, fields, api


class HealthcareAppointment(models.Model):
    _name = 'healthcare.appointment'
    _description = 'Lịch hẹn của bệnh nhân'

    patient_id = fields.Many2one('healthcare.patient', string="Bệnh nhân", required=True)
    appointment_date = fields.Datetime(string="Ngày giờ hẹn", required=True)
    note = fields.Text(string="Ghi chú")
    state = fields.Selection([
        ('scheduled', 'Đã đặt'),
        ('confirmed', 'Xác nhận'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Hủy')
    ], default='scheduled', string="Trạng thái")

    @api.model
    def send_reminder_emails(self):
        appointments = self.search([
            ('state', '=', 'scheduled'),
            ('appointment_date', '>=', fields.Datetime.now()),
        ])
        for appointment in appointments:
            template = self.env.ref('healthcare_management.email_template_appointment_reminder')
            template.send_mail(appointment.id, force_send=True)
