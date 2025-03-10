# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, timedelta


class ComplianceReport(models.Model):
    _name = 'compliance.report'
    _description = 'Báo cáo tuân thủ'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tên báo cáo', required=True, tracking=True)
    date_from = fields.Date(string='Từ ngày', required=True, tracking=True)
    date_to = fields.Date(string='Đến ngày', required=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('confirmed', 'Xác nhận'),
        ('approved', 'Phê duyệt'),
    ], string='Trạng thái', default='draft', tracking=True)

    regulation_ids = fields.Many2many('medical.regulation', string='Các quy định')
    department_ids = fields.Many2many('hr.department', string='Các phòng ban')

    user_id = fields.Many2one('res.users', string='Người lập báo cáo', default=lambda self: self.env.user,
                              tracking=True)
    confirmed_by = fields.Many2one('res.users', string='Người xác nhận', tracking=True)
    confirmed_date = fields.Date(string='Ngày xác nhận', tracking=True)
    approved_by = fields.Many2one('res.users', string='Người phê duyệt', tracking=True)
    approved_date = fields.Date(string='Ngày phê duyệt', tracking=True)

    total_checks = fields.Integer(string='Tổng số đợt kiểm tra', compute='_compute_statistics', store=True)
    compliant_checks = fields.Integer(string='Số đợt tuân thủ', compute='_compute_statistics', store=True)
    partial_checks = fields.Integer(string='Số đợt tuân thủ một phần', compute='_compute_statistics', store=True)
    non_compliant_checks = fields.Integer(string='Số đợt không tuân thủ', compute='_compute_statistics', store=True)

    compliance_percentage = fields.Float(string='Tỷ lệ tuân thủ (%)', compute='_compute_statistics', store=True)

    check_ids = fields.Many2many('compliance.check', string='Các đợt kiểm tra', compute='_compute_check_ids',
                                 store=True)
    corrective_action_ids = fields.Many2many('corrective.action', string='Các hành động khắc phục',
                                             compute='_compute_corrective_action_ids', store=True)

    summary = fields.Text(string='Tóm tắt báo cáo', tracking=True)
    conclusion = fields.Text(string='Kết luận', tracking=True)
    recommendation = fields.Text(string='Khuyến nghị', tracking=True)

    @api.depends('date_from', 'date_to', 'regulation_ids', 'department_ids')
    def _compute_check_ids(self):
        for record in self:
            domain = [('check_date', '>=', record.date_from), ('check_date', '<=', record.date_to)]

            if record.regulation_ids:
                domain.append(('regulation_id', 'in', record.regulation_ids.ids))

            if record.department_ids:
                domain.append(('department_id', 'in', record.department_ids.ids))

            record.check_ids = self.env['compliance.check'].search(domain)

    @api.depends('check_ids')
    def _compute_corrective_action_ids(self):
        for record in self:
            record.corrective_action_ids = self.env['corrective.action'].search([
                ('compliance_check_id', 'in', record.check_ids.ids)
            ])

    @api.depends('check_ids', 'check_ids.result')
    def _compute_statistics(self):
        for record in self:
            record.total_checks = len(record.check_ids)
            record.compliant_checks = len(record.check_ids.filtered(lambda x: x.result == 'compliant'))
            record.partial_checks = len(record.check_ids.filtered(lambda x: x.result == 'partial'))
            record.non_compliant_checks = len(record.check_ids.filtered(lambda x: x.result == 'non_compliant'))

            if record.total_checks > 0:
                # Tính toán tỷ lệ tuân thủ: (compliant + partial*0.5) / total
                record.compliance_percentage = ((record.compliant_checks + (
                            record.partial_checks * 0.5)) / record.total_checks) * 100
            else:
                record.compliance_percentage = 0

    def action_confirm(self):
        self.state = 'confirmed'
        self.confirmed_by = self.env.user.id
        self.confirmed_date = fields.Date.today()

    def action_approve(self):
        self.state = 'approved'
        self.approved_by = self.env.user.id
        self.approved_date = fields.Date.today()

    def action_draft(self):
        self.state = 'draft'

    def action_generate_summary(self):
        """Tự động tạo tóm tắt báo cáo dựa trên dữ liệu"""
        for record in self:
            summary = _("""
Trong giai đoạn từ %s đến %s, đã thực hiện %s đợt kiểm tra tuân thủ.
- Số đợt tuân thủ hoàn toàn: %s (%s%%)
- Số đợt tuân thủ một phần: %s (%s%%)
- Số đợt không tuân thủ: %s (%s%%)
Tỷ lệ tuân thủ tổng thể: %s%%
            """) % (
                record.date_from.strftime('%d/%m/%Y'),
                record.date_to.strftime('%d/%m/%Y'),
                record.total_checks,
                record.compliant_checks,
                round(record.compliant_checks / record.total_checks * 100 if record.total_checks else 0, 2),
                record.partial_checks,
                round(record.partial_checks / record.total_checks * 100 if record.total_checks else 0, 2),
                record.non_compliant_checks,
                round(record.non_compliant_checks / record.total_checks * 100 if record.total_checks else 0, 2),
                round(record.compliance_percentage, 2)
            )

            # Thêm thông tin về hành động khắc phục
            actions_in_progress = len(
                record.corrective_action_ids.filtered(lambda x: x.state in ['draft', 'in_progress']))
            actions_completed = len(
                record.corrective_action_ids.filtered(lambda x: x.state in ['completed', 'verified']))

            summary += _("""
Tổng số hành động khắc phục: %s
- Đã hoàn thành/Đã xác minh: %s
- Đang thực hiện/Dự thảo: %s
            """) % (
                len(record.corrective_action_ids),
                actions_completed,
                actions_in_progress
            )

            record.summary = summary