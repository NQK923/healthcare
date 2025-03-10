# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class CorrectiveAction(models.Model):
    _name = 'corrective.action'
    _description = 'Hành động khắc phục'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên hành động', required=True, tracking=True)
    compliance_check_id = fields.Many2one('compliance.check', string='Đợt kiểm tra', required=True, tracking=True)
    regulation_id = fields.Many2one(related='compliance_check_id.regulation_id', string='Quy định', store=True)

    description = fields.Text(string='Mô tả', tracking=True)

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Hoàn thành'),
        ('verified', 'Đã xác minh'),
    ], string='Trạng thái', default='draft', tracking=True)

    responsible_user_id = fields.Many2one('res.users', string='Người chịu trách nhiệm', tracking=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban thực hiện', tracking=True)

    start_date = fields.Date(string='Ngày bắt đầu', tracking=True)
    deadline = fields.Date(string='Hạn hoàn thành', tracking=True)
    completion_date = fields.Date(string='Ngày hoàn thành', tracking=True)

    result = fields.Text(string='Kết quả thực hiện', tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Tài liệu đính kèm')

    verify_user_id = fields.Many2one('res.users', string='Người xác minh', tracking=True)
    verify_date = fields.Date(string='Ngày xác minh', tracking=True)
    verify_note = fields.Text(string='Ghi chú xác minh', tracking=True)

    def action_start(self):
        self.state = 'in_progress'
        self.start_date = fields.Date.today()

    def action_complete(self):
        self.state = 'completed'
        self.completion_date = fields.Date.today()

    def action_verify(self):
        self.state = 'verified'
        self.verify_user_id = self.env.user.id
        self.verify_date = fields.Date.today()

    def action_reset(self):
        self.state = 'draft'