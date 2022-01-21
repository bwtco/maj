from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
from odoo.tools.translate import _


class VendorQuotation(models.Model):
    _name = 'vendor.quotation'
    _description = 'Vendor Quotation'

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        if st_id:
            return st_id.id

    def change_state(self, context={}):
        if context.get('copy') == True:
            self.write({'state': 'confirm'})
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

    READONLY_STATES = {
        'confirm': [('readonly', True)],
    }

    name = fields.Char(
        'Order Reference', required=True, select=True, copy=False, default='New')
    origin = fields.Char('Source Document', copy=False,
                         help='Reference of the document that generated this purchase order request (e.g. a sale order or an internal procurement request)')

    date_order = fields.Datetime('Quotation Date', required=True, select=True, copy=False, default=fields.Datetime.now(),
                                 help='Depicts the date where the Quotation should be validated and converted into a purchase order.',
                                 states=READONLY_STATES)
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, change_default=True, track_visibility='always',
                                 states=READONLY_STATES)
    partner_ref = fields.Char('Reference', copy=False, states=READONLY_STATES, help="Reference of the sales order or bid sent by the vendor. "
                                                                                    "It's used to do the matching when you receive the "
                                                                                    "products as this reference is usually written on the "
                                                                                    "delivery order sent by your vendor.")
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    stage_id = fields.Many2one(
        'stage.master', 'Stage', default=_default_stage, readonly=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    order_line = fields.One2many(
        'vendor.quotation.line', 'order_id', string='Order Lines', copy=True, states=READONLY_STATES)
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_tax = fields.Monetary(
        string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(
        string='Total', store=True, readonly=True, compute='_amount_all')
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string='Fiscal Position', oldname='fiscal_position')
    valid_till = fields.Datetime('Valid Till', states=READONLY_STATES)
    transport_amount = fields.Float('Transport Amount', states=READONLY_STATES)
    loading_charges = fields.Float('Loading Charges', states=READONLY_STATES)
    unloading_charges = fields.Float(
        'Unloading Charges', states=READONLY_STATES)
    other_charges = fields.Float('Other Charges', states=READONLY_STATES)
    payment_term_id = fields.Many2one(
        'account.payment.term', 'Payment Term', states=READONLY_STATES)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, index=1, default=lambda self: self.env.user.company_id.id,
                                 states=READONLY_STATES)
    use_in_quotation = fields.Boolean(
        'Use In Quotation', states=READONLY_STATES)
    delivery_schedule = fields.Datetime(
        string='Delivery Schedule', states=READONLY_STATES)
    host_name = fields.Char(string='Host Name', states=READONLY_STATES)
    flag = fields.Boolean('Flag', default=False)
    mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage', domain=lambda self: [('model', '=', self._name)], auto_join=True,
                                readonly=True)

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'vendor.quotation') or '/'
        existing_stage = []
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        msg_ids = {
            'date': datetime.now(),
            'from_stage': None,
            'to_stage': st_id.id,
            'remark': 'Created by ' + (self.env['res.users'].browse(self._context.get('uid'))).name,
            'model': 'vendor.quotation'
        }
        existing_stage.append((0, 0, msg_ids))
        vals.update({'mesge_ids': existing_stage})
        return super(VendorQuotation, self).create(vals)

    def unlink(self):
        list_ids = []
        for line in self:
            list_ids.append(line.name)
        Purchase_order_obj = self.env['quotation.details'].search(
            [('name', 'in', list_ids)])
        if Purchase_order_obj:
            raise UserError(
                _('You cannot delete Quotation which is used in Quotation comparison .'))
        return models.Model.unlink(self)


class VendorQuotationLine(models.Model):
    _name = 'vendor.quotation.line'
    _description = 'Vendor Quotation Line'

    @api.model
    def _default_category(self):
        category_obj = self.env['product.category'].search(
            [('name', '=', 'All')], limit=1)
        if category_obj:
            return category_obj.id

    name = fields.Text(string='Description')
    product_qty = fields.Float(string='Quantity', digits=dp.get_precision(
        'Product Unit of Measure'), required=True, default=1)
    date_planned = fields.Datetime(string='Scheduled Date', select=True)
    taxes_id = fields.Many2many(
        'account.tax', 'vendor_quot_line__tax_rel', 'tax_id', 'vendor_quot_line_id', string='Taxes')
    product_uom = fields.Many2one('uom.uom', string='Unit', required=True)
    product_id = fields.Many2one(
        'product.product', string='Material', change_default=True, required=True)
    price_unit = fields.Float(
        string='Rate', required=True, digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Monetary(
        compute='_compute_amount', string='Discounted Rate', store=True)
    price_total = fields.Monetary(
        compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Monetary(
        compute='_compute_amount', string='Tax', store=True)
    order_id = fields.Many2one(
        'vendor.quotation', string='Order Reference', select=True, required=True, ondelete='cascade')
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account', domain=[('account_type', '=', 'normal')])
    company_id = fields.Many2one(
        'res.company', related='order_id.company_id', string='Company', store=True, readonly=True)
    state = fields.Selection(related='order_id.state', stored=True)
#     invoice_lines = fields.One2many(
#         'account.invoice.line', 'purchase_line_id', string='Invoice Lines', readonly=True, copy=False)
    partner_id = fields.Many2one(
        'res.partner', related='order_id.partner_id', string='Partner', readonly=True, store=True)
    currency_id = fields.Many2one(
        related='order_id.currency_id', store=True, string='Currency', readonly=True)
    currency_rate = fields.Float('Currency Rate')
    date_order = fields.Datetime(
        related='order_id.date_order', string='Order Date', readonly=True)
#     procurement_ids = fields.One2many(
#         'procurement.order', 'purchase_line_id', string='Associated Procurements', copy=False)
    brand_id = fields.Many2one('brand.brand', 'Brand')
    negotiated_rate = fields.Float('Negotiated Rate')
    credit_period = fields.Integer('Credit Period')
    discount = fields.Float(
        string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
    product_category = fields.Many2one(
        'uom.category', 'Material Category', required=True, default=_default_category)
    taxed_amount = fields.Monetary(
        string='Taxed Amount', store=True, readonly=True, compute='_compute_amount')
    basic_amount = fields.Monetary(
        string='Basic Amount', store=True, readonly=True, compute='_compute_amount')
    net_rate = fields.Monetary(
        string='Net Rate', store=True, compute='_compute_amount')

    @api.onchange('product_category')
    def _onchage_order_line(self):
        category_ids = []
        if not self.order_id:
            return
        part = self.order_id.partner_id
        query = "select category_id from partner_prod_category_rel where partner_id={}".format(
            part.id)
        self.env.cr.execute(query)
        result = self._cr.fetchall()
        for i in result:
            category_ids.append(i[0])
        return {'domain': {'product_category': [('id', 'in', category_ids)]}}

    @api.onchange('product_id')
    def onchange_product_id(self):
        # print("\n \n self-----------------------",self)
        result = {}
        if not self.product_id:
            return result
        # Reset date, price and quantity since _onchange_quantity will provide
        # default values
        self.date_planned = datetime.today().strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        self.price_unit = self.product_qty = 1
        # print("\n \n product upm as-------------",self.product_id.uom_id)
        self.product_uom = self.product_id.uom_id
        
        # print("\n \n product upm as-------------",self.product_id.uom_id)
        self.price_unit = self.product_id.product_tmpl_id.lst_price
        result['domain'] = {
            'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        return result

    @api.depends('product_qty', 'discount', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        """
        Compute the amounts of the VQ line.
        """
        for line in self:
            tax_amount = 0
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_qty, product=line.product_id,
                                              partner=line.order_id.partner_id)
            for tax in taxes['taxes']:
                tax_amount = tax_amount + tax['amount']
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
                'taxed_amount': tax_amount,
                'basic_amount': (line.price_unit * line.product_qty),
                'net_rate': taxes['total_excluded'] + tax_amount,
            })
