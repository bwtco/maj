from datetime import datetime
from odoo import api, fields, models


class Purchase_Debit_Recovey(models.Model):
    _name = 'purchase.debit'
    _description = 'Purchase Debit Recovey'

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        return st_id

    def change_state(self, context={}):
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

    project_id = fields.Many2one('project.project', string='Project')
    project_wbs = fields.Many2one('project.task', 'project WBS Name', domain=[
                                  ('is_wbs', '=', True), ('is_task', '=', False)])
    sub_project = fields.Many2one('sub.project', 'Sub Project')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order')
    company_id = fields.Many2one(
        'res.company', string='Company ID', required=True)
    stage_id = fields.Many2one(
        'stage.master', 'Stage', default=_default_stage, readonly=True, copy=False)
    mesge_ids = fields.One2many(
        'mail.messages', 'res_id', string='Massage', domain=lambda self: [('model', '=', self._name)])
    debit_line_ids = fields.One2many(
        'purchase.debit.line', 'debit_recovery_line_id')

    @api.model
    def create(self, vals):
        rec = super(Purchase_Debit_Recovey, self).create(vals)
        context = dict(self._context or {})

        st_id = self.env['stage.master'].search([('draft', '=', True)])

        vals = {
            'date': datetime.now(),
            'from_stage': st_id.id,
            'to_stage': st_id.id,
            'remark': 'Created by ' + (self.env['res.users'].browse(self._context.get('uid'))).name,
            'model': 'purchase.debit',
            'res_id': rec.id,
        }
        re = self.env['mail.messages'].create(vals)

        return rec

    def compute_debit(self):
        self.debit_line_ids.unlink()
        data_lst = []
        old_line = [line for line in self.debit_line_ids]

        domain = []
        if self.project_id:
            domain.append(('project_id', '=', self.project_id.id))

        if self.project_wbs:
            domain.append(('project_wbs', '=', self.project_wbs.id))

        if self.sub_project:
            domain.append(('sub_project', '=', self.sub_project.id))

        if self.supplier_id:
            domain.append(('supplier_id', '=', self.supplier_id.id))

        if self.purchase_order_id:
            domain.append(('id', '=', self.purchase_order_id.id))

        purchaseorder_obj = self.env['purchase.order'].search(domain)
        for line in purchaseorder_obj:
            if (line.project_id.company_id == self.company_id):
                vals = {'project_id': line.project_id.id, 'sub_project': line.sub_project.id,
                        'purchase_order_id': line.id, 'debit_recovery_line_id': self.id, }
                self.env['purchase.debit.line'].create(vals)


class Purchase_Debit_Recovey_line(models.Model):
    _name = 'purchase.debit.line'
    _description = 'Purchase Debit Recovey line'

    debit_id = fields.Many2one('purchase.transaction', 'Debit Note No')
    debit_note_number = fields.Char("Debit Note Number")
    is_use = fields.Boolean(' ')
    project_id = fields.Many2one('project.project', string='Project')
    sub_project = fields.Many2one(
        'sub.project', string='Sub Project', required=True)
    project_wbs = fields.Many2one('project.task', string='Project Wbs')
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order')
    debit_recovery_line_id = fields.Many2one(
        'purchase.debit', 'Debit Recovery')
    debit_pur_line_id = fields.Many2one('purchase.advance', 'Advance')

    debit_note_amount = fields.Float('Debit Note Amount ')
    recovered_till_date = fields.Float('Recovered Till Date ')
    balance_amount = fields.Float('Balance Amount ')
    payment_mode = fields.Selection([
        ('cheque', 'Cheque'),
        ('ddno', 'D.D.NO'),
        ('neft', 'NEFT'),
        ('rtgs', 'RTGS'),
        ('cash', 'Cash'),
    ], string='Payment Mode')
    bank_name = fields.Char("Bank name")
    transaction_date = fields.Date('Transaction Date')
    condition = fields.Boolean(' ')
    payment_refrence = fields.Char("Cheque/DD/UTR No.")
    total_recovery = fields.Float('Total Recovery ')
    this_bill_recovery = fields.Float('This Bill Recovery ', default=0)
