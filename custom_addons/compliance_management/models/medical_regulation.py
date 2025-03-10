# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, timedelta


class MedicalRegulation(models.Model):
    _name = 'medical.regulation'
    _description = 'Quy định Y tế'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên quy định', required=True, tracking=True)
    code = fields.Char(string='Mã quy định', tracking=True)
    description = fields.Text(string='Mô tả', tracking=True)

    regulation_type = fields.Selection([
        ('national', 'Quốc gia'),
        ('international', 'Quốc tế'),
        ('local', 'Địa phương'),
    ], string='Loại quy định', default='national', tracking=True)

    issuing_authority = fields.Char(string='Cơ quan ban hành', tracking=True)
    issue_date = fields.Date(string='Ngày ban hành', tracking=True)
    effective_date = fields.Date(string='Ngày có hiệu lực', tracking=True)
    expiry_date = fields.Date(string='Ngày hết hiệu lực', tracking=True)

    document_url = fields.Char(string='Link tài liệu', tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Tài liệu đính kèm')

    compliance_check_ids = fields.One2many('compliance.check', 'regulation_id', string='Các đợt kiểm tra tuân thủ')

    is_active = fields.Boolean(string='Còn hiệu lực', default=True, tracking=True)

    responsible_department_id = fields.Many2one('hr.department', string='Phòng ban chịu trách nhiệm')
    responsible_user_id = fields.Many2one('res.users', string='Người chịu trách nhiệm', tracking=True)

    compliance_criteria_ids = fields.One2many('compliance.criteria', 'regulation_id', string='Tiêu chí tuân thủ')

    @api.model
    def _cron_check_regulation_expiry(self):
        """Kiểm tra các quy định sắp hết hạn và gửi thông báo"""
        today = date.today()
        expiry_soon = today + timedelta(days=30)

        regulations = self.search([
            ('expiry_date', '>=', today),
            ('expiry_date', '<=', expiry_soon),
            ('is_active', '=', True)
        ])

        for regulation in regulations:
            days_left = (regulation.expiry_date - today).days

            if regulation.responsible_user_id:
                regulation.message_post(
                    body=_('Quy định này sẽ hết hạn sau %s ngày!') % days_left,
                    partner_ids=[regulation.responsible_user_id.partner_id.id]
                )


class ComplianceCriteria(models.Model):
    _name = 'compliance.criteria'
    _description = 'Tiêu chí tuân thủ'

    name = fields.Char(string='Tiêu chí', required=True)
    description = fields.Text(string='Mô tả')
    regulation_id = fields.Many2one('medical.regulation', string='Quy định')
    sequence = fields.Integer(string='Thứ tự', default=10)