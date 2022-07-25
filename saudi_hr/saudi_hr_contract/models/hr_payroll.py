# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import api, models, fields, _


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.depends('contract_id')
    def check_signon_deduction(self):
        """
            Return signon_deduction amount based on contract
        """
        slip_obj = self.env['hr.payslip']
        total_amt_deduct = 0.00
        employee_id = self.contract_id.employee_id
        if employee_id.date_of_leave and employee_id.duration_in_months < 13 and employee_id.date_of_leave < datetime.now().date():
            for slip_id in slip_obj.search([('state', '=', 'done')]):
                for slip_line_id in slip_id.line_ids:
                    if slip_line_id.code == 'SIGNON':
                        total_amt_deduct += slip_line_id.total
        return total_amt_deduct

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _compute_worked_days_line_ids(self):
        res = super(HrPayslip, self)._compute_worked_days_line_ids()
        for rec in self:
            rec.input_line_ids = False
            if not rec.employee_id.date_of_leave and rec.contract_id.signon_bonus_amount > 0:
                for period in rec.contract_id.period_ids:
                    if len(rec.contract_id.period_ids) > 0:
                        signon_amt = rec.contract_id.signon_bonus_amount / len(rec.contract_id.period_ids)
                        if period.date_start == rec.date_from or period.date_stop == rec.date_to:
                            rec.write({'input_line_ids': [(0, 0, {
                                    'payslip_id': rec.id,
                                    'sequence': 2,
                                    'input_type_id': self.env.ref('saudi_hr_contract.signon_bonuse_other_input').id,
                                    'amount': signon_amt,
                                    'contract_id': rec.contract_id.id
                                })]})
            signon_amount = rec.check_signon_deduction()
            if signon_amount > 0:
                self.env['hr.payslip.input'].create({
                                    'payslip_id': rec.id,
                                    'sequence': 2,
                                    'input_type_id': self.env.ref('saudi_hr_contract.signon_deduction_other_input').id,
                                    'amount': signon_amount,
                                    'contract_id': rec.contract_id.id
                                })
        return res
