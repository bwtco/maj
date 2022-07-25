# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, models, fields, tools, _


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def action_payslip_done(self):
        """
            sent the status of generating record his/her payslip in 'done' state
        """
        res = super(HrPayslip, self).action_payslip_done()
        for payslip in self:
            expense_ids = self.get_expenses(payslip.employee_id, payslip.date_from, payslip.date_to)
            for expense in expense_ids:
                expense.slip_id = payslip.id
                expense.sheet_id.state = 'done'
        return res

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _compute_worked_days_line_ids(self):
        res = super()._compute_worked_days_line_ids()
        for rec in self:
            if rec.state in ['draft', 'verify']:
                expense_sheet_ids = self.env['hr.expense.sheet'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('state', '=', 'approve'),
                    ('payment_mode', 'in', ['own_account', 'company_account']),])

                expense_type = self.env.ref('hr_payroll_expense.expense_other_input', raise_if_not_found=False)
                expense_deduction_type = self.env.ref('hr_expense_payment.expense_deduction_other_input', raise_if_not_found=False)
                if not expense_type or not expense_deduction_type:
                    return
                if expense_sheet_ids:
                    exp_total = sum(sheet.total_amount for sheet in expense_sheet_ids.filtered(lambda l: l.payment_mode == 'own_account' and not l.payslip_id))
                    exp_ded_total = sum(sheet.total_amount for sheet in expense_sheet_ids.filtered(lambda l: l.payment_mode == 'company_account' and not l.payslip_id))
                    if not exp_total and not exp_ded_total:
                        return
                    lines_to_keep = rec.input_line_ids.filtered(lambda x: x.input_type_id != expense_type and x.input_type_id != expense_deduction_type)
                    input_lines_vals = [(4, line.id, False) for line in lines_to_keep]
                    input_lines_vals.append((0, 0, {'amount': exp_total,'input_type_id': expense_type.id}))
                    input_lines_vals.append((0, 0, {'amount': exp_ded_total,'input_type_id': expense_deduction_type.id}))
                    rec.update({'input_line_ids': input_lines_vals})
        return res

    def get_expenses(self, employee_id, date_from, date_to):
        """
            Return expenses based on employee_id, date_from and date_to
        """
        expense_sheet_ids = self.env['hr.expense.sheet'].search([('employee_id', '=', employee_id.id),
                                                                 ('state', 'in', ['post', 'done'])])
        if expense_sheet_ids:
            expense_line_ids = self.env['hr.expense'].search([('sheet_id', 'in', expense_sheet_ids.ids)])
            if expense_line_ids:
                expense_ids = expense_line_ids.filtered(lambda expense: expense.include_salary and not expense.slip_id and expense.date >= date_from and expense.date <= date_to)
                return expense_ids
        return []
