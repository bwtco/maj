from datetime import datetime
from odoo import api, fields, models


class AccountInvoice(models.Model):
    # invoice to move===============
    _inherit = "account.move"

    _description = 'Account Invoice'

    retention_amt = fields.Float(string='Retention')
    credit_sum = fields.Float(string='Credit sum')
    recovery_sum = fields.Float(string='Recovery sum')
    ra_bill_invoice = fields.Boolean(string='RA Bill?')

    project_id = fields.Many2one('project.project', string='Project', required=False)
    project_wbs_id = fields.Many2one('project.task', string='Project WBS Name', domain=[
                                     ('is_wbs', '=', True), ('project_id', '!=', False)], required=False)
    grn_ids = fields.Many2many('stock.picking', 'picking_invoice_rel', 'invoice_id', 'picking_id', string="Picking Details")

    flag = fields.Boolean(string='Flag')

    mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage', domain=lambda self: [
                                ('model', '=', self._name)], auto_join=True, readonly=True)

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        if st_id:
            return st_id.id

    stage_id = fields.Many2one('stage.master', 'Stage', default=_default_stage)

    """ OLD METHOD COMMENTED"""
#     @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice')
#     def _compute_amount(self):
#         self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
#         self.amount_tax = sum(line.amount for line in self.tax_line_ids)
#         self.amount_total = self.amount_untaxed + self.amount_tax + self.credit_sum - self.recovery_sum - self.retention_amt
#         amount_total_company_signed = self.amount_total
#         amount_untaxed_signed = self.amount_untaxed
#         if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
#             currency_id = self.currency_id.with_context(date=self.date_invoice)
#             amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
#             amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
#         sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
#         self.amount_total_company_signed = amount_total_company_signed * sign
#         self.amount_total_signed = self.amount_total * sign
#         self.amount_untaxed_signed = amount_untaxed_signed * sign
#
#         round_curr = self.currency_id.round
#         self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
#         self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
#         self.amount_total = self.amount_untaxed + self.amount_tax
#         amount_total_company_signed = self.amount_total
#         amount_untaxed_signed = self.amount_untaxed
#         if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
#             currency_id = self.currency_id
#             amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())
#             amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())
#         sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
#         self.amount_total_company_signed = amount_total_company_signed * sign
#         self.amount_total_signed = self.amount_total * sign
#         self.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.model
    def create(self, vals):
        existing_stage = []
        st_id = self.env['stage.master'].search([('draft', '=', True)])

        # invoice to move===============
        msg_ids = {
            'date': datetime.now(),
            'from_stage': None,
            'to_stage': st_id.id,
            'remark': 'Created by ' + str(self.env['res.users'].browse(self._uid).name),
            'model': 'account.move'
        }
        existing_stage.append((0, 0, msg_ids))
        vals.update({'mesge_ids': existing_stage})
        return super(AccountInvoice, self).create(vals)

    def change_state(self, context={}):
        if context.get('copy') == True:
            self.flag = True
        else:
            view_id = self.env.ref('pragtech_contracting.approval_wizard_form_view_contracting').id
            return {

                'type': 'ir.actions.act_window',
                'key2': 'client_action_multi',
                'res_model': 'approval.wizard',
                'multi': 'True',
                'target': 'new',
                'views': [[view_id, 'form']],
            }
