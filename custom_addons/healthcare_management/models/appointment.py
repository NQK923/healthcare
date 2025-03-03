from odoo import models, fields, api
from datetime import timedelta

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
        now = fields.Datetime.now()
        now_dt = fields.Datetime.from_string(now)
        three_days_later_dt = now_dt + timedelta(days=3)
        three_days_later = fields.Datetime.to_string(three_days_later_dt)

        appointments = self.search([
            ('state', '=', 'scheduled'),
            ('appointment_date', '>=', now),
            ('appointment_date', '<=', three_days_later)
        ])

        for appointment in appointments:
            patient_name = appointment.patient_id.name
            appointment_date = appointment.appointment_date.strftime('%d/%m/%Y %H:%M')
            email_to = appointment.patient_id.email

            email_values = {
                'email_to': email_to,
                'email_cc': '',
                'subject': 'Nhắc nhở lịch hẹn',
                'auto_delete': False,
                'body_html': f"""
                    <p>Chào {patient_name},</p>
                    <p>Đây là nhắc nhở về lịch hẹn của bạn vào ngày <strong>{appointment_date}</strong>.</p>
                    <p>Xin vui lòng xác nhận hoặc liên hệ nếu cần thay đổi lịch hẹn.</p>
                    <p>Trân trọng,</p>
                    <p>Đội ngũ chăm sóc sức khỏe</p>
                """
            }

            template = self.env.ref('healthcare_management.email_template_appointment_reminder')
            template.send_mail(appointment.id, force_send=True, email_values=email_values)
            appointment.write({'state': 'confirmed'})
