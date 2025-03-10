# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date


class ComplianceCheck(models.Model):
    _name = 'compliance.check'
    _description = 'Kiểm tra tuân thủ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'check_date desc, id desc'

    name = fields.Char(string='Tên đợt kiểm tra', required=True, tracking=True)
    regulation_id = fields.Many2one('medical.regulation', string='Quy định', required=True, tracking=True)
    check_date = fields.Date(string='Ngày kiểm tra', default=fields.Date.today, tracking=True)

    state = fields.Selection([
        ('draft', 'Dự thảo'),
        ('in_progress', 'Đang thực hiện'),
        ('completed', 'Hoàn thành'),
        ('non_compliant', 'Không tuân thủ'),
    ], string='Trạng thái', default='draft', tracking=True)

    responsible_user_id = fields.Many2one('res.users', string='Người kiểm tra', default=lambda self: self.env.user,
                                          tracking=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban được kiểm tra', tracking=True)

    result = fields.Selection([
        ('compliant', 'Tuân thủ'),
        ('partial', 'Tuân thủ một phần'),
        ('non_compliant', 'Không tuân thủ'),
    ], string='Kết quả', tracking=True)

    result_description = fields.Text(string='Mô tả kết quả', tracking=True)
    corrective_action_ids = fields.One2many('corrective.action', 'compliance_check_id', string='Hành động khắc phục')

    check_item_ids = fields.One2many('compliance.check.item', 'compliance_check_id', string='Danh mục kiểm tra')

    compliance_score = fields.Float(string='Điểm tuân thủ (%)', compute='_compute_compliance_score', store=True)
    next_check_date = fields.Date(string='Ngày kiểm tra tiếp theo', tracking=True)

    @api.depends('check_item_ids.is_compliant')
    def _compute_compliance_score(self):
        for record in self:
            total_items = len(record.check_item_ids)
            if total_items > 0:
                compliant_items = len(record.check_item_ids.filtered(lambda x: x.is_compliant))
                record.compliance_score = (compliant_items / total_items) * 100
            else:
                record.compliance_score = 0

    @api.onchange('regulation_id')
    def _onchange_regulation_id(self):
        if self.regulation_id and self.state == 'draft':
            # Tạo danh mục kiểm tra từ tiêu chí của quy định
            self.check_item_ids = [(5, 0, 0)]  # Xóa danh mục hiện tại
            for criteria in self.regulation_id.compliance_criteria_ids:
                self.check_item_ids = [(0, 0, {
                    'name': criteria.name,
                    'description': criteria.description,
                    'criteria_id': criteria.id,
                })]

    def action_start(self):
        self.state = 'in_progress'

    def action_complete(self):
        if not self.check_item_ids:
            raise UserError(_('Cần có ít nhất một mục kiểm tra trước khi hoàn thành.'))

        if self.compliance_score == 100:
            self.result = 'compliant'
        elif self.compliance_score > 0:
            self.result = 'partial'
        else:
            self.result = 'non_compliant'

        if self.result != 'compliant':
            self.state = 'non_compliant'
        else:
            self.state = 'completed'

    def action_draft(self):
        self.state = 'draft'

    def action_create_corrective_action(self):
        return {
            'name': _('Tạo hành động khắc phục'),
            'type': 'ir.actions.act_window',
            'res_model': 'corrective.action',
            'view_mode': 'form',
            'context': {
                'default_compliance_check_id': self.id,
                'default_name': _('Khắc phục cho %s') % self.name,
            },
        }


class ComplianceCheckItem(models.Model):
    _name = 'compliance.check.item'
    _description = 'Mục kiểm tra tuân thủ'
    _order = 'sequence, id'

    name = fields.Char(string='Tên mục', required=True)
    description = fields.Text(string='Mô tả')
    compliance_check_id = fields.Many2one('compliance.check', string='Đợt kiểm tra')
    criteria_id = fields.Many2one('compliance.criteria', string='Tiêu chí')

    is_compliant = fields.Boolean(string='Tuân thủ')
    notes = fields.Text(string='Ghi chú')

    sequence = fields.Integer(string='Thứ tự', default=10)
    evidence_ids = fields.Many2many('ir.attachment', string='Bằng chứng đính kèm')