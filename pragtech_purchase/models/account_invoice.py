from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo import api, fields, models


class AccountInvoice(models.Model):
    # changed account.invoice to account.move
    _inherit = "account.move"
    _description = 'Account Invoice'

    @api.model
    def _default_project_wbs(self):
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id'):
            return self.env['purchase.order'].browse(self._context.get('active_id')).project_wbs

    @api.model
    def _default_project(self):
        if self._context.get('active_model') == 'purchase.order' and self._context.get('active_id'):
            return self.env['purchase.order'].browse(self._context.get('active_id')).project_id

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        if st_id:
            return st_id.id

    project_id = fields.Many2one('project.project', 'Project', required=False, )
    project_wbs_id = fields.Many2one('project.task', 'Project WBS Name', required=False, domain=[
        ('is_wbs', '=', True), ('project_id', '!=', False)], )
    grn_ids = fields.Many2many('stock.picking', 'picking_invoice_rel', 'invoice_id', 'picking_id',
                               string="Picking Details")
    flag = fields.Boolean('Flag')
    stage_id = fields.Many2one(
        'stage.master', 'Stage', readonly=True, copy=False)
    mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage',
                                domain=lambda self: [('model', '=', self._name)], auto_join=True,
                                readonly=True)

    #     @api.onchange('state', 'partner_id', 'invoice_line_ids')
    #     def _onchange_allowed_grn_ids(self):
    #         '''
    #         The purpose of the method is to define a domain for the available
    #         purchase orders.
    #         '''
    #         result = {}
    #
    #         # A PO can be selected only if at least one PO line is not already in
    #         # the invoice
    #         purchase_line_ids = self.invoice_line_ids.mapped('purchase_line_id')
    #         purchase_ids = self.invoice_line_ids.mapped('purchase_id').filtered(
    #             lambda r: r.order_line <= purchase_line_ids)
    #         ##print "purchase_line_idssssssssssss", purchase_line_ids
    #         ##print "purchase idsssssssssssssssss", purchase_ids
    #         result['domain'] = {'grn_ids': [
    #             ('partner_id', 'child_of', self.partner_id.id),
    #             ('id', 'not in', purchase_ids.ids),
    #         ]}
    #         ##print "result=========================================", result
    #         return result

    @api.model
    def create(self, vals):
        existing_stage = []
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        created_by = self.env['res.users'].browse(self._uid).name
        msg_ids = {
            'date': datetime.now(),
            'from_stage': None,
            'to_stage': st_id.id,
            'remark': 'Created by {}'.format(str(created_by)),
            'model': 'account.invoice'
        }
        existing_stage.append((0, 0, msg_ids))
        vals.update({'mesge_ids': existing_stage})
        res = super(AccountInvoice, self).create(vals)
        return res

    def change_state(self, context={}):
        if context.get('copy') == True:
            self.flag = True
        else:
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

    def compute_picking(self):
        # print("context-----------------------",self._context)
        self.onchange_vendor_id()

    @api.onchange('partner_id', 'project_id', 'project_wbs_id')
    def onchange_vendor_id(self):
        return {'domain': {
            'grn_ids': [('project_id', '=', self.project_id.id), ('project_wbs', '=', self.project_wbs_id.id),
                        ('partner_id', '=', self.partner_id.id), ('state', 'in', ['done'])]}}

    @api.onchange('grn_ids')
    @api.depends('grn_ids')
    def onchange_grn_ids(self):
        data_lst = []
        tax_ids = []
        for grn in self.grn_ids:
            purchase_obj = self.env['purchase.order'].search(
                [('name', '=', grn.origin)])
            for moves in grn.move_lines:
                for line in moves.move_line_ids:
                    purchase_line = self.env['purchase.order.line'].search(
                        [('order_id', '=', purchase_obj.id), ('product_id', '=', line.product_id.id)])
                    for tax_id in purchase_line.taxes_id:
                        tax_ids.append(tax_id.id)
                    # print("line.product_id.id================",line.product_id.name,type(line.product_id.name))
                    data = {
                        'purchase_id': grn.po_id.id,
                        'purchase_line_id': purchase_line.id,
                        'name': str(line.product_id.name),
                        'product_id': line.product_id.id,
                        'account_id': self.account_id.id,
                        'quantity': line.qty_done,
                        'uom_id': line.product_uom_id.id,
                        'price_unit': purchase_line.price_unit,
                        'invoice_line_tax_ids': [(6, 0, tax_ids)],
                        'picking_id': line.picking_id.id,
                        'partner_id': purchase_line.order_id.partner_id.id,
                        'project_id': purchase_line.order_id.project_id.id,
                        'project_wbs_id': purchase_line.order_id.project_id.id,
                    }
                    data_lst.append((0, 0, data))
        self.update({'invoice_line_ids': data_lst})


class AccountInvoiceLine(models.Model):
    # changed account.invoice.line to account.move.line
    _inherit = "account.move.line"
    _description = "Account Invoice Line"

    #     @api.model
    #     def _default_account(self):
    #         if self._context.get('journal_id'):
    #             journal = self.env['account.journal'].browse(
    #                 self._context.get('journal_id'))
    #             if self._context.get('type') in ('out_invoice', 'in_refund'):
    #                 return journal.default_credit_account_id.id
    #             return journal.default_debit_account_id.id

    remark = fields.Text('Remark')
    #     name = fields.Text(string='Description', readonly=True)
    #     product_id = fields.Many2one('product.product', string='Product',
    #                                  ondelete='restrict', index=True, readonly=True)
    #     account_id = fields.Many2one('account.account', string='Account',
    #                                  required=True, domain=[
    #                                      ('deprecated', '=', False)],
    #
    #                                  help="The income or expense account related to the selected product.", readonly=True)
    # #     default=_default_account,
    #     uom_id = fields.Many2one('product.uom', string='Unit of Measure',
    #                              ondelete='set null', index=True, oldname='uos_id', readonly=True)
    #     price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision(
    #         'Product Price'), readonly=True)
    #     discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'),
    #                             default=0.0, readonly=True)
    #     invoice_line_tax_ids = fields.Many2many('account.tax',
    #                                             'account_invoice_line_tax', 'invoice_line_id', 'tax_id',
    #                                             string='Taxes', domain=[('type_tax_use', '!=', 'none')], oldname='invoice_line_tax_id', readonly=True)
    #     account_analytic_id = fields.Many2one('account.analytic.account',
    #                                           string='Analytic Account', readonly=True)
    picking_id = fields.Many2one('stock.picking', string="Picking")
