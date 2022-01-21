from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Res Partner'

    contractor = fields.Boolean(
        'Is a Contractor', help='Check this box if this contact is a Contractor.')
    cst_no = fields.Char('CST No')
    vat_no = fields.Char('VAT / TIN No')
    weekly_off = fields.Char('Weekly Off')
    credit_capacity = fields.Float('Credit Capacity')
    grading = fields.Char('Grading')
    pan_no = fields.Char('PAN No')
    registration_date = fields.Date('Registration Date')
    organization_type = fields.Many2one(
        'organization.type', 'Organization Type')
    vendor_status = fields.Selection([('trial', 'Trial'), ('approved', 'Approved'), (
        'suspended', 'Suspended'), ('black_listed', 'Black Listed')], 'Vendor Status', default='trial')
    trial_allowed = fields.Integer("Trials Allowed", default=3)
    trial_used = fields.Integer("Trials Used", compute='_get_trial')
    status_remark = fields.Text(string='Status Remark')
    vendor_type = fields.Selection(
        [('supplier', 'Supplier'), ('contractor', 'Contractor')], 'Vendor Type')
    group_id = fields.Char('Group ID')
    inbusiness_since = fields.Char('InBusiness Since')
    turn_over = fields.Float('Annual Turn Over')
    number_of_employees = fields.Integer('Number of employees')
    remark = fields.Char('Remark')
    website = fields.Char('Website')
    primary_supplier = fields.Char('Primary Supplier')
    wct_no = fields.Char('WCT No')
    shop_act_no = fields.Char('Shop Act No')
    shop_act_expiry_date = fields.Date('Shop Act Expiry Date')
    pf_code_registration_no = fields.Char(' PF Code Registration No ')
    esic_no = fields.Char('ESIC Number')
    lwmf_no = fields.Integer('LWMF Number')
    categ_ids = fields.One2many('product.category', 'part_id', 'Partner')
    attachment_line_ids = fields.One2many(
        'ir.attachment', 'partner_id', 'Attachment Lines')
    service_tax_no = fields.Integer('Service tax No.')

    material_category = fields.Many2many(
        'product.category', 'partner_prod_category_rel', 'partner_id', 'category_id')
    chk_is_supplier=fields.Boolean(string="Customer/Supplier",default=False)

    @api.depends('trial_allowed')
    def _get_trial(self):
        domain = []
        count = 0
        context=self._context
        if "res_partner_search_mode" in context:
            partner_search_mode = self.env.context.get('res_partner_search_mode')
            for val in self:
                val.trial_used = 0
                if partner_search_mode == 'supplier':
                    self.chk_is_supplier=True
                    domain.append(('partner_id', '=', val.id))
                    domain.append(
                        ('state', 'in', ('shipment', 'purchase', 'done')))
                    po_obj = self.env['purchase.order'].search(domain)
                    for po in po_obj:
                        count = count + 1
                    val.trial_used = count

                elif partner_search_mode == 'customer':
                    self.chk_is_supplier=False
                
        else:
            for val in self:
                val.trial_used = 0
            


    def write(self, vals):
        remark_string = ""
        if vals.get('vendor_status'):
            ##print "yes status ............"
            status = vals.get('vendor_status')
            remark_string = 'Status changed by ' + \
                (self.env['res.users'].browse(
                    self._context.get('uid'))).name + ' to ' + status
            if vals.get('status_remark'):
                ##print "yes remark ........"
                remark = vals.get('status_remark')
                remark_string = remark_string + ' for ' + remark
                #print remark_string

        if (remark_string):
            msg_ids = {
                'date': datetime.now(),
                'remark': remark_string,
                # 'body': remark_string,
                'author_id': self._context.get('uid'),
                'model': 'res.partner',
                'res_id': self.id,
            }
            cret = self.env['mail.messages'].create(msg_ids)
        return super(ResPartner, self).write(vals)


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    _description = 'Res Partner Bank'
    mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage', domain=lambda self: [('model', '=', self._name)], auto_join=True,
                                readonly=True)

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        remark = vals.copy()
        remark_string = ""
        if remark.get(u'acc_number'):
            remark['Account Number'] = remark.pop(u'acc_number')
        if remark.get(u'bank_id'):
            bank_id = remark.get(u'bank_id')
            res_bank_obj = self.env['res.bank'].browse(bank_id)
            remark['Bank'] = remark.pop(u'bank_id')
            remark['Bank'] = res_bank_obj.name
        for key, value in remark.items():
            if key != 'currency_id':
                remark_string = remark_string + \
                    "{}: {}".format(key, value) + ','
        data = []
        msg_ids = {
            'date': datetime.now(),
            'remark': remark_string,
            'author_id': self._context.get('uid'),
            'model': 'res.partner.bank'
        }
        data.append((0, 0, msg_ids))
        vals.update({'mesge_ids': data})
        return models.Model.create(self, vals)

    def write(self, vals):
        remark_string = ""
        remark = vals.copy()
        if remark.get(u'acc_number'):
            remark['Account Number'] = remark.pop(u'acc_number')
        if remark.get(u'bank_id'):
            bank_id = remark.get(u'bank_id')
            res_bank_obj = self.env['res.bank'].browse(bank_id)
            remark['Bank'] = remark.pop(u'bank_id')
            remark['Bank'] = res_bank_obj.name
        for key, value in remark.items():
            remark_string = remark_string + "{}: {}".format(key, value) + ','
        msg_ids = {
            'date': datetime.now(),
            'remark': remark_string,
            'author_id': self._context.get('uid'),
            'model': 'res.partner.bank',
            'res_id': self.id,
        }
        self.env['mail.messages'].create(msg_ids)
        return models.Model.write(self, vals)


class ProductCategory(models.Model):
    _inherit = 'product.category'
    _description = 'Product Category'

    part_id = fields.Many2one('res.partner', 'Partner Id')


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    _description = 'Ir Attachment'

    partner_id = fields.Many2one('res.partner', 'Document ID')
