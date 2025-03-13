# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import ValidationError


class PatientFeedback(models.Model):
    _name = 'healthcare.patient.feedback'
    _description = 'Phản hồi của bệnh nhân'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Mã phản hồi', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Bệnh nhân', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban', tracking=True)
    feedback_date = fields.Date(string='Ngày phản hồi', default=fields.Date.context_today, tracking=True)
    feedback_type = fields.Selection([
        ('compliment', 'Khen ngợi'),
        ('suggestion', 'Góp ý'),
        ('complaint', 'Khiếu nại'),
        ('question', 'Hỏi đáp'),
        ('other', 'Khác')
    ], string='Loại phản hồi', required=True, tracking=True)

    description = fields.Text(string='Nội dung phản hồi', required=True)
    state = fields.Selection([
        ('draft', 'Mới'),
        ('in_progress', 'Đang xử lý'),
        ('resolved', 'Đã giải quyết'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)

    resolution = fields.Text(string='Phương án giải quyết')
    resolved_date = fields.Date(string='Ngày giải quyết')
    user_id = fields.Many2one('res.users', string='Người phụ trách', default=lambda self: self.env.user)

    satisfaction_rating = fields.Selection([
        ('1', 'Rất không hài lòng'),
        ('2', 'Không hài lòng'),
        ('3', 'Bình thường'),
        ('4', 'Hài lòng'),
        ('5', 'Rất hài lòng')
    ], string='Đánh giá mức độ hài lòng')

    complaint_id = fields.Many2one('healthcare.patient.complaint', string='Khiếu nại liên quan')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('healthcare.patient.feedback') or _('New')
        return super(PatientFeedback, self).create(vals_list)

    def action_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_resolved(self):
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Date.context_today(self)
        })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_create_complaint(self):
        self.ensure_one()
        return {
            'name': _('Tạo khiếu nại mới'),
            'type': 'ir.actions.act_window',
            'res_model': 'healthcare.patient.complaint',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_feedback_id': self.id,
                'default_description': self.description,
            }
        }


class PatientComplaint(models.Model):
    _name = 'healthcare.patient.complaint'
    _description = 'Khiếu nại của bệnh nhân'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Mã khiếu nại', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Bệnh nhân', required=True, tracking=True)
    complaint_date = fields.Date(string='Ngày khiếu nại', default=fields.Date.context_today, tracking=True)

    description = fields.Text(string='Nội dung khiếu nại', required=True)
    state = fields.Selection([
        ('draft', 'Mới'),
        ('investigating', 'Đang xử lý'),
        ('resolved', 'Đã giải quyết'),
        ('closed', 'Đã đóng'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)

    priority = fields.Selection([
        ('0', 'Thấp'),
        ('1', 'Trung bình'),
        ('2', 'Cao')
    ], string='Mức độ ưu tiên', default='1', tracking=True)

    category = fields.Selection([
        ('service', 'Dịch vụ'),
        ('staff', 'Nhân viên'),
        ('facility', 'Cơ sở vật chất'),
        ('billing', 'Thanh toán'),
        ('other', 'Khác')
    ], string='Phân loại khiếu nại', required=True, tracking=True)

    feedback_id = fields.Many2one('healthcare.patient.feedback', string='Phản hồi liên quan')
    user_id = fields.Many2one('res.users', string='Người phụ trách', default=lambda self: self.env.user)

    resolution = fields.Text(string='Phương án giải quyết')
    action_taken = fields.Text(string='Biện pháp thực hiện')

    resolved_date = fields.Date(string='Ngày giải quyết')
    deadline = fields.Date(string='Hạn chót', compute='_compute_deadline', store=True)
    is_overdue = fields.Boolean(string='Quá hạn', compute='_compute_is_overdue', store=True)

    satisfaction_rating = fields.Selection([
        ('1', 'Rất không hài lòng'),
        ('2', 'Không hài lòng'),
        ('3', 'Bình thường'),
        ('4', 'Hài lòng'),
        ('5', 'Rất hài lòng')
    ], string='Đánh giá mức độ hài lòng')

    @api.depends('complaint_date', 'priority')
    def _compute_deadline(self):
        for record in self:
            if record.complaint_date:
                if record.priority == '2':  # Cao
                    record.deadline = record.complaint_date + timedelta(days=3)
                elif record.priority == '1':  # Trung bình
                    record.deadline = record.complaint_date + timedelta(days=7)
                else:  # Thấp
                    record.deadline = record.complaint_date + timedelta(days=14)
            else:
                record.deadline = False

    @api.depends('deadline')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = record.deadline and record.deadline < today and record.state not in ['resolved',
                                                                                                     'closed',
                                                                                                     'cancelled']

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('healthcare.patient.complaint') or _('New')
        return super(PatientComplaint, self).create(vals_list)

    def action_investigate(self):
        self.write({'state': 'investigating'})

    def action_resolve(self):
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Date.context_today(self)
        })

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})