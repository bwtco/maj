# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    def _compute_worked_days_line_ids(self):
        res = super()._compute_worked_days_line_ids()
        for rec in self:
            bonus_line_obj = self.env['employee.bonus.lines']
            bonus_line_ids = bonus_line_obj.search([('employee_id', '=', rec.employee_id.id), ('state', 'in', ['done'])])
            for line in bonus_line_ids:
                bonus_amount = line.bonus
                if len(line.period_ids) > 0:
                    bonus_amount = line.bonus / len(line.period_ids)
                for period in line.period_ids:
                    if period.date_start == rec.date_from or period.date_stop == rec.date_to:
                        bonus_type = self.env.ref('saudi_hr_bonus.bonus_input', raise_if_not_found=False)
                        lines_to_keep = rec.input_line_ids.filtered(lambda x: x.input_type_id != bonus_type)
                        input_lines_vals = [(4, line.id, False) for line in lines_to_keep]
                        input_lines_vals.append((0, 0, {'amount': bonus_amount,'input_type_id': bonus_type.id}))
                        rec.update({'input_line_ids': input_lines_vals})
        return res
