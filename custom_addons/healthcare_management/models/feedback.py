from datetime import timedelta

from odoo import models, fields, api


class HealthcareFeedback(models.Model):
    _name = 'healthcare.feedback'
    _description = 'Phản hồi của bệnh nhân'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Mã phản hồi", required=True, copy=False, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('healthcare.feedback.sequence'))
    patient_id = fields.Many2one('healthcare.patient', string="Bệnh nhân", required=True)
    feedback_type = fields.Selection([
        ('service', 'Chất lượng dịch vụ'),
        ('doctor', 'Bác sĩ'),
        ('facility', 'Cơ sở vật chất'),
        ('staff', 'Nhân viên'),
        ('price', 'Giá cả'),
        ('other', 'Khác')
    ], string="Loại phản hồi", required=True, default='service')

    feedback = fields.Text(string="Nội dung phản hồi", required=True)
    date = fields.Date(string="Ngày phản hồi", default=fields.Date.context_today)

    rating = fields.Selection([
        ('1', '1 - Rất không hài lòng'),
        ('2', '2 - Không hài lòng'),
        ('3', '3 - Bình thường'),
        ('4', '4 - Hài lòng'),
        ('5', '5 - Rất hài lòng'),
    ], string="Đánh giá", required=True)

    priority = fields.Selection([
        ('0', 'Thấp'),
        ('1', 'Trung bình'),
        ('2', 'Cao'),
        ('3', 'Rất cao')
    ], string='Mức độ ưu tiên', default='1')

    appointment_id = fields.Many2one('healthcare.appointment', string="Lịch hẹn liên quan")

    state = fields.Selection([
        ('new', 'Mới'),
        ('in_review', 'Đang xem xét'),
        ('addressed', 'Đã giải quyết'),
        ('closed', 'Đã đóng')
    ], string="Trạng thái", default='new', tracking=True)

    handled_by = fields.Many2one('res.users', string="Người xử lý")
    handling_note = fields.Text(string="Ghi chú xử lý")

    @api.onchange('rating')
    def _onchange_rating(self):
        if self.rating:
            if self.rating in ['1', '2']:
                self.priority = '2'  # Cao
            elif self.rating == '3':
                self.priority = '1'  # Trung bình
            else:
                self.priority = '0'  # Thấp


# Thêm các phương thức này vào model HealthcareFeedback

    @api.model
    def create(self, vals):
        # Nếu độ ưu tiên không được thiết lập và có đánh giá
        if 'priority' not in vals and 'rating' in vals:
            if vals['rating'] in ['1', '2']:
                vals['priority'] = '2'  # Cao
            elif vals['rating'] == '3':
                vals['priority'] = '1'  # Trung bình
            else:
                vals['priority'] = '0'  # Thấp

        return super(HealthcareFeedback, self).create(vals)


    def action_review(self):
        self.write({
            'state': 'in_review',
            'handled_by': self.env.user.id
        })

        # Tạo hoạt động cho người xử lý
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=f"Xem xét phản hồi: {self.name}",
            note=f"Phản hồi từ bệnh nhân {self.patient_id.name} cần được xem xét và xử lý.",
            user_id=self.env.user.id,
            date_deadline=fields.Date.context_today(self) + timedelta(days=2)
        )

        return True


    def action_address(self):
        self.write({
            'state': 'addressed'
        })

        # Hoàn thành tất cả các hoạt động
        self.activity_ids.action_done()

        return True


    def action_close(self):
        self.write({
            'state': 'closed'
        })
        return True


    def action_reset(self):
        self.write({
            'state': 'new',
            'handled_by': False
        })
        return True


    def action_view_patient(self):
        return {
            'name': 'Thông tin bệnh nhân',
            'type': 'ir.actions.act_window',
            'res_model': 'healthcare.patient',
            'view_mode': 'form',
            'res_id': self.patient_id.id,
        }


    def action_view_appointment(self):
        if not self.appointment_id:
            return {}

        return {
            'name': 'Thông tin lịch hẹn',
            'type': 'ir.actions.act_window',
            'res_model': 'healthcare.appointment',
            'view_mode': 'form',
            'res_id': self.appointment_id.id,
        }