from datetime import datetime
from odoo import api, fields, models


class Purchase_Transaction(models.Model):
    _name = 'purchase.transaction'
    _description = 'Purchase Transaction'

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        if st_id:
            return st_id.id

    name = fields.Char(
        'Transaction No.', states={'draft': [('readonly', False)]}, copy=False,)
    project_id = fields.Many2one(
        'project.project', string='Project', required=True)
    project_wbs = fields.Many2one('project.task', 'project WBS Name', domain=[
                                  ('is_wbs', '=', True), ('is_task', '=', False)], required=False)
    sub_project = fields.Many2one('sub.project', 'Sub Project', required=False)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order', required=True)
    transaction_type = fields.Selection(
        [('debit_note', 'Debit Note'), ('advance', 'Advance')], string='Transaction Type', required=True)
    bank_name = fields.Char("Bank Name")
    narration = fields.Char("Narration")
    transaction_remark = fields.Text(string='Transaction Remark')
    amount = fields.Integer(string="Amount")
    commencement_date = fields.Datetime('Commencement Date')
    maximum_advance = fields.Float('Maximum Advance(%)')
    wct_account = fields.Many2one(
        'account.analytic.account', string='WCT Account')
    completion_date = fields.Datetime('Completion Date')
    tds_account = fields.Many2one(
        'account.analytic.account', string='TDS Account')
    title = fields.Char('Title')
    wct_percent = fields.Float('WCT(%)')
    stage_id = fields.Many2one(
        'stage.master', 'Stage', default=_default_stage, readonly=True, copy=False)
    mesge_ids = fields.One2many(
        'mail.messages', 'res_id', string='Massage', domain=lambda self: [('model', '=', self._name)])
    flag = fields.Boolean(' ')
    recovered_count = fields.Integer(
        string='# of Recoveries', compute='get_recovered_records_count')

    recovered_till_date = fields.Float('Recovered Till Date ')
    balance_amount = fields.Float(
        'Balance Amount ', compute='get_balance_amount')

    counter = 0

    @api.depends('amount', 'recovered_till_date')
    def get_balance_amount(self):
        self.balance_amount = self.amount - self.recovered_till_date

    @api.onchange('purchase_order_id')
    def on_change_work_order_id(self):
        order = self.env['purchase.order'].search(
            [('id', '=', self.purchase_order_id.id)])
        for line in order:
            self.project_id = line.project_id.id
            self.sub_project = line.sub_project.id

    @api.model
    def create(self, vals):
        t_type = vals.get('transaction_type')
        wo_id = vals.get('purchase_order_id')
        amount = vals.get('amount')

        rec = super(Purchase_Transaction, self).create(vals)
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        vals = {
            'date': datetime.now(),
            'from_stage': st_id.id,
            'to_stage': st_id.id,
            'remark': 'Created by ' + (self.env['res.users'].browse(self._context.get('uid'))).name,
            'model': 'purchase.transaction',
            'res_id': rec.id,
        }
        re = self.env['mail.messages'].create(vals)
        return rec

    def change_state(self, context={}):
        if self.counter == 0:
            self.counter = self.counter + 1
            if context.get('copy') == True:
                self.flag = True
                if self.transaction_type == 'advance':
                    self.name = self.env['ir.sequence'].next_by_code(
                        'transaction.advance.purchase') or '/'
                    """updating advanced amount in WO"""
                if self.transaction_type == 'debit_note':
                    self.name = self.env['ir.sequence'].next_by_code(
                        'transaction.debit.purchase') or '/'
                    """updating debited amount in WO"""
            else:
                self.flag = False
            view_id = self.env.ref(
                'pragtech_purchase.approval_wizard_form_view_purchase').id
            return {
                'type': 'ir.actions.act_window',
                'key2': 'client_action_multi',
                'res_model': 'approval.wizard',
                'multi': 'True',
                'target': 'new',
                'views': [[view_id, 'form']],
            }
    """Return only count of recovery ids"""

    def get_recovered_records_count(self):
        recovered_count = 0
        st_id = self.env['stage.master'].search([('approved', '=', True)])
        if self.transaction_type == 'advance':
            self.recovered_count = self.env['purchase.advance.line'].search_count(
                [('advance_id', '=', self.id)])
        elif self.transaction_type == 'debit_note':
            self.recovered_count = self.env['purchase.debit.line'].search_count(
                [('debit_id', '=', self.id)])

    """Return recovery records(tree view)"""
    def get_recoveries(self):
        recovery_ids = []
        st_id = self.env['stage.master'].search([('approved', '=', True)])

        if self.transaction_type == 'debit_note':
            action = self.env.ref('pragtech_purchase.purchase_action_advance')
            recovery_line_obj = self.env['purchase.debit.line'].search(
                [('debit_id', '=', self.id)])
            for line in recovery_line_obj:
                recovery_ids.append(line.debit_pur_line_id.id)
            view_id = self.env.ref(
                'pragtech_purchase.purchase_advance_view_tree').id
            model = 'purchase.advance'
        elif self.transaction_type == 'advance':
            action = self.env.ref('pragtech_purchase.purchase_action_advance')
            recovery_line_obj = self.env['purchase.advance.line'].search(
                [('advance_id', '=', self.id)])
            for line in recovery_line_obj:
                recovery_ids.append(line.advance_recovery_line_id.id)
            view_id = self.env.ref(
                'pragtech_purchase.purchase_advance_view_tree').id
            model = 'purchase.advance'

        return {'name': 'Recoveries',
                'domain': [('id', 'in', recovery_ids)],
                # 'view_type': action.view_type,
                'view_mode': action.view_mode,
                'res_model': model,
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                }
