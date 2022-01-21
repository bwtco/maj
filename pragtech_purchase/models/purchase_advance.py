from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError


class Purchase_Advance(models.Model):
    _name = 'purchase.advance'
    _description = 'Purchase Advance'

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        return st_id

    name = fields.Char('Name')
    project_id = fields.Many2one('project.project', string='Project')
    project_wbs = fields.Many2one('project.task', 'Project WBS', domain=[
                                  ('is_wbs', '=', True), ('is_task', '=', False)])
    sub_project = fields.Many2one('sub.project', 'Sub Project')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order')
    company_id = fields.Many2one(
        'res.company', string='Company ID', required=True)
    advance_line_ids = fields.One2many(
        'purchase.advance.line', 'advance_recovery_line_id')
    stage_id = fields.Many2one(
        'stage.master', 'Stage', default=_default_stage, readonly=True, copy=False)
    mesge_ids = fields.One2many(
        'mail.messages', 'res_id', string='Massage', domain=lambda self: [('model', '=', self._name)])
    flag = fields.Boolean(' ')

    debit_adv_line_ids = fields.One2many(
        'purchase.debit.line', 'debit_pur_line_id')

    total_adv_rec = fields.Float('Total Advance Received', compute='get_total')
    total_deb_rec = fields.Float('Total Debit Received', compute='get_total')
    total_payable = fields.Float('Total Payable', compute='get_total')
    counter = 0

    @api.model
    def create(self, vals):
        rec = super(Purchase_Advance, self).create(vals)
        context = dict(self._context or {})

        st_id = self.env['stage.master'].search([('draft', '=', True)])
        remark = 'Created by ' + \
            (self.env['res.users'].browse(self._context.get('uid'))).name,

        vals = {
            'date': datetime.now(),
            'from_stage': st_id.id,
            'to_stage': st_id.id,
            'remark': 'Created by ' + (self.env['res.users'].browse(self._context.get('uid'))).name,
            'model': 'purchase.advance',
            'res_id': rec.id,
        }
        re = self.env['mail.messages'].create(vals)
        return rec

    @api.depends('advance_line_ids.balance_amount', 'advance_line_ids.is_use', 'debit_adv_line_ids.balance_amount', 'debit_adv_line_ids.is_use')
    def get_total(self):
        total = 0
        for line in self.advance_line_ids:
            if line.is_use:
                total += line.this_bill_recovery
        self.total_adv_rec = total

        total = 0
        for line in self.debit_adv_line_ids:
            if line.is_use:
                total += line.this_bill_recovery
        self.total_deb_rec = total

        self.total_payable = self.total_adv_rec + self.total_deb_rec

    def compute_advance(self):
        self.advance_line_ids.unlink()
        self.debit_adv_line_ids.unlink()
        data_lst = []
        old_line = [line for line in self.advance_line_ids]
        domain = []
        domain.append(('transaction_type', '=', 'debit_note'))
        if self.project_id:
            domain.append(('project_id', '=', self.project_id.id))

        if self.project_wbs:
            domain.append(('project_wbs', '=', self.project_wbs.id))

        if self.sub_project:
            domain.append(('sub_project', '=', self.sub_project.id))

        if self.supplier_id:
            domain.append(('partner_id', '=', self.supplier_id.id))

        if self.purchase_order_id:
            domain.append(('purchase_order_id', '=', self.purchase_order_id.id))
        #print domain
        advances = self.env['purchase.transaction'].search(domain)
        #print advances
        st_id = self.env['stage.master'].search([('approved', '=', True)])
        for line in advances:
            #print line
            recovered_till_date = 0
            approved_recovery_obj = self.search([('stage_id', '=', st_id.id)])
            for approved_recovery in approved_recovery_obj:
                for approved_line in approved_recovery.debit_adv_line_ids:
                    if approved_line.is_use:
                        if approved_line.debit_id.id == line.id:
                            recovered_till_date = recovered_till_date + \
                                approved_line.balance_amount
            if (line.project_id.company_id == self.company_id):
                if line.balance_amount > 0:
                    vals = {'debit_id': line.id, 'debit_note_number': line.name, 'debit_note_amount': line.amount, 'project_id': line.project_id.id, 'sub_project': line.sub_project.id,
                            'purchase_order_id': line.purchase_order_id.id, 'debit_pur_line_id': self.id, 'recovered_till_date': line.recovered_till_date, 'balance_amount': line.balance_amount}
                    self.env['purchase.debit.line'].create(vals)

        domain.remove(('transaction_type', '=', 'debit_note'))
        domain.append(('transaction_type', '=', 'advance'))

        advances_new = self.env['purchase.transaction'].search(domain)
        st_id = self.env['stage.master'].search([('approved', '=', True)])
        for line in advances_new:
            recovered_till_date = 0
            approved_recovery_obj = self.search([('stage_id', '=', st_id.id)])
            for approved_recovery in approved_recovery_obj:
                for approved_line in approved_recovery.advance_line_ids:
                    if approved_line.is_use:
                        if approved_line.advance_id.id == line.id:
                            recovered_till_date = recovered_till_date + \
                                approved_line.balance_amount
            if (line.project_id.company_id == self.company_id):
                if line.balance_amount > 0:
                    vals = {'advance_id': line.id, 'advance_amount': line.amount, 'project_id': line.project_id.id, 'sub_project': line.sub_project.id, 'purchase_order_id':
                            line.purchase_order_id.id, 'advance_recovery_line_id': self.id, 'recovered_till_date': line.recovered_till_date, 'balance_amount': line.balance_amount}
                    self.env['purchase.advance.line'].create(vals)

    def change_state(self, context={}):
        if self.counter == 0:
            self.counter = self.counter + 1
            selected_lines = []
            if context.get('copy') == True:
                self.name = self.env['ir.sequence'].next_by_code(
                    'purchase.recovery.independent.of.bill') or '/'
                self.flag = True
                for line in self.advance_line_ids:
                    if line.is_use:
                        selected_lines.append(line.is_use)
                        line.transaction_date = datetime.now().date()
                    if not line.is_use:
                        line.unlink()
                for line in self.debit_adv_line_ids:
                    if line.is_use:
                        selected_lines.append(line.is_use)
                        line.transaction_date = datetime.now().date()
                    if not line.is_use:
                        line.unlink()
                if len(selected_lines) == 0:
                    raise UserError('Please select at least one record to approve')

                """Updating recovery till date in transaction"""
                for adv in self.advance_line_ids:
                    adv_obj = self.env['purchase.transaction'].browse(
                        adv.advance_id.id)
                    if(adv.this_bill_recovery <= adv.balance_amount):
                        adv_obj.recovered_till_date = adv_obj.recovered_till_date + \
                            adv.this_bill_recovery
                    else:
                        raise UserError('This Bill recovery cannot be greater then balance amount')

                for deb in self.debit_adv_line_ids:
                    debit_obj = self.env[
                        'purchase.transaction'].browse(deb.debit_id.id)
                    if(deb.this_bill_recovery <= deb.balance_amount):
                        debit_obj.recovered_till_date = debit_obj.recovered_till_date + \
                            deb.this_bill_recovery
                    else:
                        raise UserError('This Bill recovery cannot be greater then balance amount')

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

    def unlink(self):
        st_id = self.env['stage.master'].search([('approved', '=', True)])
        for line in self:
            if line.stage_id.id == st_id.id:
                raise UserError('You cannot delete approved records')

        return models.Model.unlink(self)


class Purchase_Advanceline(models.Model):
    _name = 'purchase.advance.line'
    _description = 'Purchase Advance line'

    name = fields.Char(' ')
    advance_id = fields.Many2one('purchase.transaction', 'Advance Note No')
    is_use = fields.Boolean(' ')
    project_id = fields.Many2one('project.project', string='Project')
    sub_project = fields.Many2one(
        'sub.project', string='Sub Project', required=True)
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Purchase Order')

    advance_recovery_line_id = fields.Many2one('purchase.advance', 'Advance')
#     bill_id=fields.Many2one('ra.bill','Bill')

    advance_amount = fields.Float('Advance Amount ')
    recovered_till_date = fields.Float('Recovered Till Date ')
    balance_amount = fields.Float('Balance Amount ')
    total_recovery = fields.Float('Total Recovery ')
    this_bill_recovery = fields.Float('This Bill Recovery ', default=0)
    is_use = fields.Boolean(' ')

    payment_mode = fields.Selection([
        ('cheque', 'Cheque'),
        ('ddno', 'D.D.NO'),
        ('neft', 'NEFT'),
        ('rtgs', 'RTGS'),
        ('cash', 'Cash'),
    ], string='Payment Mode')
    bank_name = fields.Char("Bank name")
    transaction_date = fields.Date('Transaction Date')
    payment_refrence = fields.Char("Cheque/DD/UTR No.")
