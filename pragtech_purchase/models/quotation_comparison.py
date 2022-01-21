from datetime import datetime, timedelta, date
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.exceptions import UserError
from odoo.tools.translate import _


class QuotationComparison(models.Model):
    _name = 'quotation.comparison'
    _rec_name = 'project_id'
    _description = 'Quotation Comparison'

    @api.model
    def _default_stage(self):
        st_id = self.env['stage.master'].search([('draft', '=', True)])
        if st_id:
            return st_id.id

    project_id = fields.Many2one('project.project', 'Project', required=True)
    project_wbs_id = fields.Many2one('project.task', 'Project WBS Name', required=True, domain=[
                                     ('is_wbs', '=', True), ('project_id', '!=', False)])

    sub_project = fields.Many2one('sub.project', 'Sub Project', required=True)

    sequence_name = fields.Char(
        'Comparison Reference', required=True, select=True, copy=False, default='New')
    from_date = fields.Datetime(
        'From Date', default=str(date.today() - timedelta(days=15)))
    to_date = fields.Datetime(
        'To Date', default=str(date.today() + timedelta(days=1)))
    material_line = fields.One2many(
        'material.list', 'quotation_comp_mat_id', string='Material Lines', copy=True)
    vendors_line = fields.One2many(
        'supplier.list', 'quotation_comp_sup_id', string='Vendor Lines', copy=True)
    quotation_details = fields.One2many(
        'quotation.details', 'quotation_comp_detail_id', string='Quotation Lines', copy=True)
    quotation_comp_particular = fields.One2many(
        'quotation.compare.particular', 'quotation_comp_pert_id', string='Quotation Details Line', copy=True)
    total_amount = fields.Float(
        string='Total Amount', store=True, compute='compute_total_amount')
    quotation_comp_vendor1 = fields.One2many(
        'quotation.compare.vendor1', 'quotation_comp_ven1_id', string='Quotation Details Vendor1', copy=True)
    quotation_comp_vendor2 = fields.One2many(
        'quotation.compare.vendor2', 'quotation_comp_ven2_id', string='Quotation Details Vendor2', copy=True)
    quotation_comp_vendor3 = fields.One2many(
        'quotation.compare.vendor3', 'quotation_comp_ven3_id', string='Quotation Details Vendor3', copy=True)
    quotation_comp_vendor4 = fields.One2many(
        'quotation.compare.vendor4', 'quotation_comp_ven4_id', string='Quotation Details Vendor4', copy=True)
    quotation_comp_vendor5 = fields.One2many(
        'quotation.compare.vendor5', 'quotation_comp_ven5_id', string='Quotation Details Vendor6', copy=True)
    quotation_comp_vendor6 = fields.One2many(
        'quotation.compare.vendor6', 'quotation_comp_ven6_id', string='Quotation Details Vendor6', copy=True)
    quotation_comp_tax_particular = fields.One2many('tax.particular', 'quotation_comp_taxper_id', string='Quotation Tax Particular Details',
                                                    copy=True)
    quotation_comp_tax_details1 = fields.One2many(
        'tax.details.vendor1', 'quotation_comp_tax1_id', string='Quotation Tax1 Details', copy=True)
    quotation_comp_tax_details2 = fields.One2many(
        'tax.details.vendor2', 'quotation_comp_tax2_id', string='Quotation Tax2 Details', copy=True)
    quotation_comp_tax_details3 = fields.One2many(
        'tax.details.vendor3', 'quotation_comp_tax3_id', string='Quotation Tax3 Details', copy=True)
    quotation_comp_tax_details4 = fields.One2many(
        'tax.details.vendor4', 'quotation_comp_tax4_id', string='Quotation Tax4 Details', copy=True)
    quotation_comp_tax_details5 = fields.One2many(
        'tax.details.vendor5', 'quotation_comp_tax5_id', string='Quotation Tax5 Details', copy=True)
    quotation_comp_tax_details6 = fields.One2many(
        'tax.details.vendor6', 'quotation_comp_tax6_id', string='Quotation Tax6 Details', copy=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Comparison Confirm'),
    ], string='Status', copy=False, index=True, track_visibility='onchange', default='draft')

    flag = fields.Boolean('Flag', default=False)
    mesge_ids = fields.One2many('mail.messages', 'res_id', string='Massage')
    stage_id = fields.Many2one(
        'stage.master', 'Stage', default=_default_stage, copy=False)
    total_vendor1 = fields.Float(
        "Total", store=True, compute='_amount_particular_all')
    total_vendor2 = fields.Float(
        "Total", store=True, compute='_amount_particular_all')
    total_vendor3 = fields.Float(
        "Total", store=True, compute='_amount_particular_all')
    total_vendor4 = fields.Float(
        "Total", store=True, compute='_amount_particular_all')
    total_vendor5 = fields.Float(
        "Total", store=True, compute='_amount_particular_all')
    total_vendor6 = fields.Float(
        "Total", store=True, compute='_amount_particular_all')

    tax_id = fields.Many2many(
        'account.tax', 'quotation_com_tax_rel', 'tax_id', 'quot_com_id', string='Taxes')

    vendor1 = fields.Many2one(
        'res.partner', 'Vendor1', domain=[('supplier', '=', True)])
    vendor2 = fields.Many2one(
        'res.partner', 'Vendor2', domain=[('supplier', '=', True)])
    vendor3 = fields.Many2one(
        'res.partner', 'Vendor3', domain=[('supplier', '=', True)])
    vendor4 = fields.Many2one(
        'res.partner', 'Vendor4', domain=[('supplier', '=', True)])
    vendor5 = fields.Many2one(
        'res.partner', 'Vendor5', domain=[('supplier', '=', True)])
    vendor6 = fields.Many2one(
        'res.partner', 'Vendor6', domain=[('supplier', '=', True)])
    selected_vendors = fields.Integer(
        compute='get_selected_vendors', string='No Of vendors')
    description1 = fields.Char('')
    description2 = fields.Char('')
    description3 = fields.Char('')
    description4 = fields.Char('')

    @api.depends('vendors_line', 'vendors_line.is_vendor')
    def get_selected_vendors(self):
        count = 0
        for line in self.vendors_line:
            if line.is_vendor:
                count = count + 1
        self.selected_vendors = count
        return count

    @api.onchange('project_id')
    def onchange_project_id(self):
        self.sub_project = False
        sub_project_ids = []
        sub_project_obj = self.env['sub.project'].search(
            [('project_id', '=', self.project_id.id)])
        for line in sub_project_obj:
            sub_project_ids.append(line.id)
        return {'domain': {'sub_project': [('id', 'in', sub_project_ids)]}}

    def unlink(self):
        ids = []
        for line in self:
            ids.append(line.state)
            if 'confirm' in ids:
                raise UserError(_('You cannot delete Confirmed Quotation.'))

    def confirm_action(self):
        obj = self.browse(self.id)
        obj.sequence_name = self.env[
            'ir.sequence'].next_by_code('quotation.comparison')

        no_of_approve = []
        no_of_products = [
            particular.product_id for particular in self.quotation_comp_particular if particular.is_approve]
        for vendor1 in self.quotation_comp_vendor1:
            if vendor1.is_approve:
                no_of_approve.append(vendor1.is_approve)
                product_template_obj = self.env['product.template'].search(
                    [('name', '=', vendor1.product_id.name)])
                vals = {
                    'name': vendor1.vendor_id.id,
                    'price': vendor1.negotiated_rate,
                    'min_qty': 1,
                    'product_name': vendor1.product_id.name,
                    'product_tmpl_id': vendor1.product_id.product_tmpl_id.id,
                    'product_code': vendor1.product_id.product_tmpl_id.default_code,
                    'is_active': True,
                }
                for line in product_template_obj.seller_ids:
                    if vendor1.product_id.name == line.product_name:
                        line.write({'is_active': False})
                product_template_obj.seller_ids.sudo().create(vals)

        for vendor2 in self.quotation_comp_vendor2:
            if vendor2.is_approve:
                no_of_approve.append(vendor2.is_approve)
                product_template_obj = self.env['product.template'].search(
                    [('name', '=', vendor2.product_id.name)])
                vals = {
                    'name': vendor2.vendor_id.id,
                    'price': vendor2.negotiated_rate,
                    'min_qty': 1,
                    'product_name': vendor2.product_id.name,
                    'product_tmpl_id': vendor2.product_id.product_tmpl_id.id,
                    'product_code': vendor2.product_id.product_tmpl_id.default_code,
                    'is_active': True,
                }
                for line in product_template_obj.seller_ids:
                    if vendor2.product_id.name == line.product_name:
                        line.write({'is_active': False})
                product_template_obj.seller_ids.sudo().create(vals)

        for vendor3 in self.quotation_comp_vendor3:
            if vendor3.is_approve:
                no_of_approve.append(vendor3.is_approve)
                product_template_obj = self.env['product.template'].search(
                    [('name', '=', vendor3.product_id.name)])
                vals = {
                    'name': vendor3.vendor_id.id,
                    'price': vendor3.negotiated_rate,
                    'min_qty': 1,
                    'product_name': vendor3.product_id.name,
                    'product_tmpl_id': vendor3.product_id.product_tmpl_id.id,
                    'product_code': vendor3.product_id.product_tmpl_id.default_code,
                    'is_active': True,
                }
                for line in product_template_obj.seller_ids:
                    if vendor3.product_id.name == line.product_name:
                        line.write({'is_active': False})
                product_template_obj.seller_ids.sudo().create(vals)

        for vendor4 in self.quotation_comp_vendor4:
            if vendor4.is_approve:
                no_of_approve.append(vendor4.is_approve)
                product_template_obj = self.env['product.template'].search(
                    [('name', '=', vendor4.product_id.name)])
                vals = {
                    'name': vendor4.vendor_id.id,
                    'price': vendor4.negotiated_rate,
                    'min_qty': 1,
                    'product_name': vendor4.product_id.name,
                    'product_tmpl_id': vendor4.product_id.product_tmpl_id.id,
                    'product_code': vendor4.product_id.product_tmpl_id.default_code,
                    'is_active': True,
                }
                for line in product_template_obj.seller_ids:
                    if vendor4.product_id.name == line.product_name:
                        line.write({'is_active': False})
                product_template_obj.seller_ids.sudo().create(vals)
        for vendor5 in self.quotation_comp_vendor5:
            if vendor5.is_approve:
                no_of_approve.append(vendor5.is_approve)
                product_template_obj = self.env['product.template'].search(
                    [('name', '=', vendor5.product_id.name)])
                vals = {
                    'name': vendor5.vendor_id.id,
                    'price': vendor5.negotiated_rate,
                    'min_qty': 1,
                    'product_name': vendor5.product_id.name,
                    'product_tmpl_id': vendor5.product_id.product_tmpl_id.id,
                    'product_code': vendor5.product_id.product_tmpl_id.default_code,
                    'is_active': True,
                }
                for line in product_template_obj.seller_ids:
                    if vendor5.product_id.name == line.product_name:
                        line.write({'is_active': False})
                product_template_obj.seller_ids.sudo().create(vals)

        for vendor6 in self.quotation_comp_vendor6:
            if vendor6.is_approve:
                no_of_approve.append(vendor6.is_approve)
                product_template_obj = self.env['product.template'].search(
                    [('name', '=', vendor6.product_id.name)])
                vals = {
                    'name': vendor6.vendor_id.id,
                    'price': vendor6.negotiated_rate,
                    'min_qty': 1,
                    'product_name': vendor6.product_id.name,
                    'product_tmpl_id': vendor6.product_id.product_tmpl_id.id,
                    'product_code': vendor6.product_id.product_tmpl_id.default_code,
                    'is_active': True,
                }
                for line in product_template_obj.seller_ids:
                    if vendor6.product_id.name == line.product_name:
                        line.write({'is_active': False})
                product_template_obj.seller_ids.create(vals)

        if len(no_of_approve) != len(no_of_products) or len(no_of_products) == 0:
            raise UserError(
                _("Kindly check appropriate vendors for approval."))
        else:
            self.state = 'confirm'

    def button_dummy(self):
        return True

    @api.onchange('project_wbs_id', 'from_date', 'to_date')
    def onchange_project_wbs1(self):
        # Set material list
        material_ids = list(set(
            [material.material_id.id for material in self.project_wbs_id.material_estimate_line]))
        material_lines = []
        for material_id in material_ids:
            material_lines.append(
                (0, 0, {'material_id': material_id, 'quotation_comp_mat_id': self.id}))
        # Set vendor list
        quotation_lines = self.env['vendor.quotation.line'].search(
            [('product_id', 'in', material_ids), ('order_id.date_order', '>=', self.from_date), ('order_id.date_order', '<=', self.to_date)])
        vendor_ids = list(
            set([line.order_id.partner_id.id for line in quotation_lines]))
        vendor_lines = []
        for vendor in vendor_ids:
            vendor_obj = self.env['res.partner'].browse(vendor)
            # print "vendor_obj.vendor_status", vendor_obj.vendor_status
            if vendor_obj.vendor_status == 'suspended':
                vendor_ids.remove(vendor)
            if vendor_obj.vendor_status == 'black_listed':
                vendor_ids.remove(vendor)
        # print " after vendor_ids-----------------------------",vendor_ids
        for vendor_id in vendor_ids:
            vendor_lines.append(
                (0, 0, {'vendor_id': vendor_id, 'quotation_comp_sup_id': self.id}))
        self.update({
            'material_line': material_lines,
            'vendors_line': vendor_lines,
        })

    @api.depends('quotation_details.price_subtotal')
    def compute_total_amount(self):
        for order in self:
            total_amount = 0.0
            for line in order.quotation_details:
                total_amount += line.price_subtotal
            order.update({'total_amount': total_amount, })

    @api.depends('quotation_comp_vendor1.amount', 'quotation_comp_vendor2.amount',
                 'quotation_comp_vendor3.amount', 'quotation_comp_vendor4.amount', 'quotation_comp_vendor5.amount',
                 'quotation_comp_vendor6.amount', 'quotation_comp_tax_details1.tax', 'quotation_comp_tax_details2.tax',
                 'quotation_comp_tax_details3.tax',
                 'quotation_comp_tax_details4.tax', 'quotation_comp_tax_details5.tax', 'quotation_comp_tax_details6.tax')
    def _amount_particular_all(self):
        for order in self:
            total_vendor1 = total_vendor2 = total_vendor3 = total_vendor4 = total_vendor5 = total_vendor6 = 0.0
            total_tax_vendor1 = total_tax_vendor2 = total_tax_vendor3 = total_tax_vendor4 = total_tax_vendor5 = total_tax_vendor6 = 0.0
            for line in order.quotation_comp_vendor1:
                total_vendor1 += line.amount
            for line in order.quotation_comp_vendor2:
                total_vendor2 += line.amount
            for line in order.quotation_comp_vendor3:
                total_vendor3 += line.amount
            for line in order.quotation_comp_vendor4:
                total_vendor4 += line.amount
            for line in order.quotation_comp_vendor5:
                total_vendor5 += line.amount
            for line in order.quotation_comp_vendor6:
                total_vendor6 += line.amount
            for line in order.quotation_comp_tax_details1:
                total_tax_vendor1 += line.tax
            for line in order.quotation_comp_tax_details2:
                total_tax_vendor2 += line.tax
            for line in order.quotation_comp_tax_details3:
                total_tax_vendor3 += line.tax
            for line in order.quotation_comp_tax_details4:
                total_tax_vendor4 += line.tax
            for line in order.quotation_comp_tax_details5:
                total_tax_vendor5 += line.tax
            for line in order.quotation_comp_tax_details6:
                total_tax_vendor5 += line.tax
        order.update({
            'total_vendor1': total_vendor1 + total_tax_vendor1,
            'total_vendor2': total_vendor2 + total_tax_vendor2,
            'total_vendor3': total_vendor3 + total_tax_vendor3,
            'total_vendor4': total_vendor4 + total_tax_vendor4,
            'total_vendor5': total_vendor5 + total_tax_vendor5,
            'total_vendor6': total_vendor6 + total_tax_vendor6,
        })

    def compute_quotation_details(self):
        # Set quotation line based on selected material, vendor, date range and
        # old quotation
        counter = 0
        for material_lines in self.material_line:
            if material_lines.is_material:
                counter += 1
        if counter > 2:
            raise UserError(_("You can select maximum two products."))

        quotation_details_lines = []
        common_line_ids = []
        material_ids = [
            line.material_id.id for line in self.material_line if line.is_material]
        old_quotation_lines = [line.id for line in self.quotation_details]
        selected_vendor_ids = [
            line.vendor_id.id for line in self.vendors_line if line.is_vendor]
        if len(selected_vendor_ids) > 6:
            raise UserError(_("You can select maximum 6 vendors."))

        quotation_ids = self.env['vendor.quotation'].search([('date_order', '>=', self.from_date), ('date_order', '<=', self.to_date),
                                                             ('partner_id', 'in', selected_vendor_ids), ('state', '=', 'confirm')])
        # print ("\n\n\n\nquotation_id===========================",quotation_ids,material_ids,selected_vendor_ids)
        for quotation in quotation_ids:
            for quotation_line in quotation.order_line:
                if quotation_line.product_id.id in material_ids:
                    old_line_flag = False
                    old_line = None
                    for line in self.quotation_details:
                        if line.vendor_id.id == quotation_line.partner_id.id and line.name == quotation.name and \
                                line.product_id.id == quotation_line.product_id.id:
                            old_line_flag = True
                            old_line = line
                            break
                    if not old_line_flag:
                        vals = {
                            'name': quotation.name,
                            'date': quotation.date_order,
                            'vendor_id': quotation.partner_id.id,
                            'product_id': quotation_line.product_id.id,
                            'tax_id': quotation_line.taxes_id,
                            'tax': quotation_line.price_tax,
                            'product_qty': quotation_line.product_qty,
                            'product_uom': quotation_line.product_uom.id,
                            'price_unit': quotation_line.price_unit,
                            'negotiated_rate': quotation_line.negotiated_rate,
                            'price_subtotal': quotation_line.price_subtotal,
                        }
                        quotation_details_lines.append((0, 0, vals))
                    else:
                        # Keep old line as it is
                        quotation_details_lines.append((4, old_line.id, False))
                        common_line_ids.append(old_line.id)
        # Remove unused old lines
        for quot_id in old_quotation_lines:
            if quot_id not in common_line_ids:
                quotation_details_lines.append((2, quot_id, False))
        val = {'quotation_details': quotation_details_lines, }
        # Set selected vendor for comparison header
        for idx, vendor_id in enumerate(selected_vendor_ids, 1):
            vendor = 'vendor' + str(idx)
            val.update({vendor: vendor_id, })
        # If selected vendor is less then set other header to None
        if len(selected_vendor_ids) < 6:
            for idx in range(len(selected_vendor_ids) + 1, 7):
                vendor = 'vendor' + str(idx)
                val.update({vendor: None, })
        self.update(val)

    def get_taxes1(self):
        if self.quotation_comp_vendor1:
            tax_amount = {}
            self.quotation_comp_tax_details1.unlink()
            for vendor in self.quotation_comp_vendor1:
                for tax_line in vendor.tax_id:
                    if tax_line in tax_amount:
                        tax_amount[
                            tax_line] += (tax_line.amount / 100) * vendor.amount
                        record = self.env['tax.details.vendor1'].search(
                            [('tax_id', '=', tax_line.id), ('quotation_comp_tax1_id', '=', self.id)])
                        record.write({
                            'tax': tax_amount[tax_line],
                        })
                    else:
                        tax_amount.update(
                            {tax_line: (tax_line.amount / 100) * vendor.amount})

                        self.env['tax.details.vendor1'].create({
                            'tax_id': [(6, 0, [tax_line.id])],
                            'vendor_id': vendor.vendor_id.id,
                            'tax': tax_amount[tax_line],
                            'quotation_comp_tax1_id': self.id
                        })

        if self.quotation_comp_vendor2:
            tax_amount = {}
            self.quotation_comp_tax_details2.unlink()
            for vendor in self.quotation_comp_vendor2:
                for tax_line in vendor.tax_id:
                    if tax_line in tax_amount:
                        tax_amount[
                            tax_line] += (tax_line.amount / 100) * vendor.amount
                        record = self.env['tax.details.vendor2'].search(
                            [('tax_id', '=', tax_line.id), ('quotation_comp_tax2_id', '=', self.id)])
                        record.write({
                            'tax': tax_amount[tax_line],
                        })
                    else:
                        tax_amount.update(
                            {tax_line: (tax_line.amount / 100) * vendor.amount})

                        self.env['tax.details.vendor2'].create({
                            'tax_id': [(6, 0, [tax_line.id])],
                            'vendor_id': vendor.vendor_id.id,
                            'tax': tax_amount[tax_line],
                            'quotation_comp_tax2_id': self.id
                        })

        if self.quotation_comp_vendor3:
            tax_amount = {}
            self.quotation_comp_tax_details3.unlink()
            for vendor in self.quotation_comp_vendor3:
                for tax_line in vendor.tax_id:
                    if tax_line in tax_amount:
                        tax_amount[
                            tax_line] += (tax_line.amount / 100) * vendor.amount
                        record = self.env['tax.details.vendor3'].search(
                            [('tax_id', '=', tax_line.id), ('quotation_comp_tax3_id', '=', self.id)])
                        record.write({
                            'tax': tax_amount[tax_line],
                        })
                    else:
                        tax_amount.update(
                            {tax_line: (tax_line.amount / 100) * vendor.amount})

                        self.env['tax.details.vendor3'].create({
                            'tax_id': [(6, 0, [tax_line.id])],
                            'vendor_id': vendor.vendor_id.id,
                            'tax': tax_amount[tax_line],
                            'quotation_comp_tax3_id': self.id
                        })
        if self.quotation_comp_vendor4:
            tax_amount = {}
            self.quotation_comp_tax_details4.unlink()
            for vendor in self.quotation_comp_vendor4:
                for tax_line in vendor.tax_id:
                    if tax_line in tax_amount:
                        tax_amount[
                            tax_line] += (tax_line.amount / 100) * vendor.amount
                        record = self.env['tax.details.vendor4'].search(
                            [('tax_id', '=', tax_line.id), ('quotation_comp_tax4_id', '=', self.id)])
                        record.write({
                            'tax': tax_amount[tax_line],
                        })
                    else:
                        tax_amount.update(
                            {tax_line: (tax_line.amount / 100) * vendor.amount})

                        self.env['tax.details.vendor4'].create({
                            'tax_id': [(6, 0, [tax_line.id])],
                            'vendor_id': vendor.vendor_id.id,
                            'tax': tax_amount[tax_line],
                            'quotation_comp_tax4_id': self.id
                        })
        if self.quotation_comp_vendor5:
            tax_amount = {}
            self.quotation_comp_tax_details5.unlink()
            for vendor in self.quotation_comp_vendor5:
                for tax_line in vendor.tax_id:
                    if tax_line in tax_amount:
                        tax_amount[
                            tax_line] += (tax_line.amount / 100) * vendor.amount
                        record = self.env['tax.details.vendor5'].search(
                            [('tax_id', '=', tax_line.id), ('quotation_comp_tax5_id', '=', self.id)])
                        record.write({
                            'tax': tax_amount[tax_line],
                        })
                    else:
                        tax_amount.update(
                            {tax_line: (tax_line.amount / 100) * vendor.amount})

                        self.env['tax.details.vendor5'].create({
                            'tax_id': [(6, 0, [tax_line.id])],
                            'vendor_id': vendor.vendor_id.id,
                            'tax': tax_amount[tax_line],
                            'quotation_comp_tax5_id': self.id})

        if self.quotation_comp_vendor6:
            tax_amount = {}
            self.quotation_comp_tax_details6.unlink()
            for vendor in self.quotation_comp_vendor6:
                for tax_line in vendor.tax_id:
                    if tax_line in tax_amount:
                        tax_amount[
                            tax_line] += (tax_line.amount / 100) * vendor.amount
                        record = self.env['tax.details.vendor6'].search(
                            [('tax_id', '=', tax_line.id), ('quotation_comp_tax6_id', '=', self.id)])
                        record.write({
                            'tax': tax_amount[tax_line],
                        })
                    else:
                        tax_amount.update(
                            {tax_line: (tax_line.amount / 100) * vendor.amount})

                        self.env['tax.details.vendor6'].create({
                            'tax_id': [(6, 0, [tax_line.id])],
                            'vendor_id': vendor.vendor_id.id,
                            'tax': tax_amount[tax_line],
                            'quotation_comp_tax6_id': self.id
                        })

    def compute_quotation_details_dictionary(self):
        # Return computed Dictionary for quotation comparison
        result = {}
        if self.quotation_details:
            for line in self.quotation_details:
                if line.is_use:
                    prod_id = line.product_id.id
                    vend_id = line.vendor_id.id
                    if result.get(prod_id):
                        #                         ##print "result.get(prod_id)---------------",result.get(prod_id)
                        # Update existing Rec
                        if not result[prod_id].get(vend_id):
                            # ##print "if not------------",result[prod_id]
                            result[prod_id].update({vend_id: line})
                        else:
                            #                             ##print "else"
                            continue
                            # fix it if same partner have multiple quotation
                    else:  # Add New rec
                        # ##print "final else--------",result
                        result.update({prod_id: {vend_id: line}})
#         ##print "result===============",result
        return result

    def get_product_list(self):
        unique_products = [
            line.product_id.id for line in self.quotation_details if line.is_use]
        return list(set(unique_products))

    def compute_selected_quotations(self):
        selected_quotation = []
        if self.quotation_details:

            avg = 0
            particular_lines_list = []
            tax_list = []
            # estimated material list to get avg cost of same.
            material_lst = []
            appended_prod = []
            selected_vendor_ids = [
                line.vendor_id.id for line in self.vendors_line if line.is_vendor]
            # products used in quotation
            for line in self.quotation_details:
                prod_list = []
                cost = 0
                if line.is_use:
                    prod_list.append(line.product_id.id)
                    selected_quotation.append(line.is_use)
                    if 1 < len(set(prod_list)) < 0:
                        raise UserError(_("Please check selected products."))

                    material_lines = self.env['task.material.line'].search(
                        [('material_id', '=', line.product_id.id), ('wbs_id', '=', self.project_wbs_id.id)])
                    for material in material_lines:
                        cost += material.material_rate
                        material_lst.append(material.id)
                    avg = cost / len(material_lst)

                    # tax Particular 1
                    if not self.env['tax.particular'].search([('product_id', '=', line.product_id.id), ('quotation_comp_taxper_id', '=', self.id)]):
                        product_tax_detail_data = {
                            'product_id': line.product_id.id,
                            # 'is_approve': 0,
                        }
                        tax_list.append((0, 0, product_tax_detail_data))
                    self.update({'quotation_comp_tax_particular': tax_list})

                    #  Particular old - for odoo9
#                     obj=self.env['quotation.compare.particular'].search(
#                             [('product_id', '=', line.product_id.id),('quotation_comp_pert_id', '=', self.id)])
#                     ##print "appended_prod----------",appended_prod
#
#                     if line.product_id.id not in appended_prod:
#                         vals = {
#                             'product_id': line.product_id.id,
#                             'product_uom': line.product_uom.id,
#                             'price_expt': avg,
#                         }
#                         ##print "appending data---------------",vals,obj
#                         appended_prod.append(line.product_id.id)
#                         particular_lines_list.append((0, 0, vals))
#                     list=self.get_product_list()
#                     ##print "after called-------------",list
#
#                     for particular in self.quotation_comp_particular:
#                         if particular.product_id.id not in list:
#                             ##print "particular.product_id.id-----",particular.product_id.id
#                             particular_lines_list.append((2,particular.id))
#             self.update({'quotation_comp_particular': particular_lines_list})

        for line in self.material_line:
            if line.is_material:
                vals = {
                    'product_id': line.material_id.id,
                    'product_uom': line.material_id.uom_id.id,
                    'price_expt': avg,
                    'quotation_comp_pert_id': self.id
                }
                particulat_prod_list = [
                    i.product_id.id for i in self.quotation_comp_particular]
                if line.material_id.id not in particulat_prod_list:
                    self.env['quotation.compare.particular'].create(vals)

        """ If no quotation selected then unlink all  """
        if len(selected_quotation) == 0:
            self.quotation_comp_particular.unlink()
            self.quotation_comp_vendor1.unlink()
            self.quotation_comp_vendor2.unlink()
            self.quotation_comp_vendor3.unlink()
            self.quotation_comp_vendor4.unlink()
            self.quotation_comp_vendor5.unlink()
            self.quotation_comp_vendor6.unlink()

        try:
            quotation_compare_vendor1_list = []
            vals = {}
            old_lines = [
                line.product_id.id for line in self.quotation_comp_vendor1]
            quotation_details_dict = self.compute_quotation_details_dictionary()

            for k_parent, v_parent in quotation_details_dict.items():
                for k, v in v_parent.items():
                    if k == selected_vendor_ids[0]:
                        tax_ids = []
                        for tax_line in v.tax_id:
                            tax_ids.append(tax_line.id)

                        vals = {
                            'product_id': v.product_id.id,
                            'vendor_id': v.vendor_id.id,
                            'amount': v.price_unit,
                            'negotiated_rate': v.price_unit,
                            'quotation_comp_ven1_id': self.id,
                            'tax_id': [(6, 0, tax_ids)],
                        }
                    elif k != selected_vendor_ids[0]:
                        None
                    else:
                        blank_line1 = self.env['quotation.compare.vendor1'].search(
                            [('product_id', '=', line.product_id.id), ('vendor_id', '=', None), ('quotation_comp_ven1_id', '=', self.id)])
                        if not blank_line1:
                            vals = {
                                'product_id': line.product_id.id,
                                'vendor_id': None,
                                'amount': None,
                                'negotiated_rate': None,
                                'quotation_comp_ven1_id': self.id,
                                'tax_id': None,
                            }

                quotation_compare_vendor1_list.append((0, 0, vals))
                for quotation_comp_vendor1 in self.quotation_comp_vendor1:
                    if quotation_comp_vendor1.id not in quotation_compare_vendor1_list:
                        quotation_compare_vendor1_list.append(
                            (2, quotation_comp_vendor1.id))
                self.update(
                    {'quotation_comp_vendor1': quotation_compare_vendor1_list})

            quotation_compare_vendor2_list = []
            vals = {}
            quotation_details_dict = self.compute_quotation_details_dictionary()
            for k_parent, v_parent in quotation_details_dict.items():
                for k, v in v_parent.items():
                    if k == selected_vendor_ids[1]:
                        tax_ids = []
                        for tax_line in v.tax_id:
                            tax_ids.append(tax_line.id)

                        vals = {
                            'product_id': v.product_id.id,
                            'vendor_id': v.vendor_id.id,
                            'amount': v.price_unit,
                            'negotiated_rate': v.price_unit,
                            'quotation_comp_ven2_id': self.id,
                            'tax_id': [(6, 0, tax_ids)],
                        }
                    elif k != selected_vendor_ids[1]:
                        pass
                    else:
                        blank_line2 = self.env['quotation.compare.vendor2'].search(
                            [('product_id', '=', line.product_id.id), ('vendor_id', '=', None), ('quotation_comp_ven2_id', '=', self.id)])
                        if not blank_line2:
                            vals = {
                                'product_id': line.product_id.id,
                                'vendor_id': None,
                                'amount': None,
                                'negotiated_rate': None,
                                'quotation_comp_ven2_id': self.id,
                                'tax_id': None,
                            }
                quotation_compare_vendor2_list.append((0, 0, vals))
                for quotation_comp_vendor2 in self.quotation_comp_vendor2:
                    if quotation_comp_vendor2.id not in quotation_compare_vendor2_list:
                        quotation_compare_vendor2_list.append(
                            (2, quotation_comp_vendor2.id))
                self.update(
                    {'quotation_comp_vendor2': quotation_compare_vendor2_list})

            vals = {}
            quotation_compare_vendor3_list = []
            quotation_details_dict = self.compute_quotation_details_dictionary()
            for k_parent, v_parent in quotation_details_dict.items():
                for k, v in v_parent.items():
                    if k == selected_vendor_ids[2]:
                        tax_ids = []
                        for tax_line in v.tax_id:
                            tax_ids.append(tax_line.id)

                        vals = {
                            'product_id': v.product_id.id,
                            'vendor_id': v.vendor_id.id,
                            'amount': v.price_unit,
                            'negotiated_rate': v.price_unit,
                            'quotation_comp_ven3_id': self.id,
                            'tax_id': [(6, 0, tax_ids)],
                        }
                    elif k != selected_vendor_ids[2]:
                        pass
                    else:
                        blank_line3 = self.env['quotation.compare.vendor3'].search(
                            [('product_id', '=', line.product_id.id), ('vendor_id', '=', None), ('quotation_comp_ven3_id', '=', self.id)])
                        if not blank_line3:
                            vals = {
                                'product_id': line.product_id.id,
                                'vendor_id': None,
                                'amount': None,
                                'negotiated_rate': None,
                                'quotation_comp_ven3_id': self.id,
                                'tax_id': None,
                            }

                quotation_compare_vendor3_list.append((0, 0, vals))
                for quotation_comp_vendor3 in self.quotation_comp_vendor3:
                    if quotation_comp_vendor3.id not in quotation_compare_vendor3_list:
                        quotation_compare_vendor3_list.append(
                            (2, quotation_comp_vendor3.id))
                self.update(
                    {'quotation_comp_vendor3': quotation_compare_vendor3_list})

            quotation_compare_vendor4_list = []
            vals = {}
            quotation_details_dict = self.compute_quotation_details_dictionary()
            for k_parent, v_parent in quotation_details_dict.items():
                for k, v in v_parent.items():
                    if k == selected_vendor_ids[3]:
                        tax_ids = []
                        for tax_line in v.tax_id:
                            tax_ids.append(tax_line.id)

                        vals = {
                            'product_id': v.product_id.id,
                            'vendor_id': v.vendor_id.id,
                            'amount': v.price_unit,
                            'negotiated_rate': v.price_unit,
                            'quotation_comp_ven4_id': self.id,
                            'tax_id': [(6, 0, tax_ids)],
                        }
                    elif k != selected_vendor_ids[3]:
                        pass
                    else:
                        blank_line4 = self.env['quotation.compare.vendor4'].search(
                            [('product_id', '=', line.product_id.id), ('vendor_id', '=', None), ('quotation_comp_ven4_id', '=', self.id)])
                        if not blank_line4:
                            vals = {
                                'product_id': line.product_id.id,
                                'vendor_id': None,
                                'amount': None,
                                'negotiated_rate': None,
                                'quotation_comp_ven4_id': self.id,
                                'tax_id': None,
                            }

                quotation_compare_vendor4_list.append((0, 0, vals))
                for quotation_comp_vendor4 in self.quotation_comp_vendor4:
                    if quotation_comp_vendor4.id not in quotation_compare_vendor4_list:
                        quotation_compare_vendor4_list.append(
                            (2, quotation_comp_vendor4.id))
                self.update(
                    {'quotation_comp_vendor4': quotation_compare_vendor4_list})

            quotation_compare_vendor5_list = []
            vals = {}
            quotation_details_dict = self.compute_quotation_details_dictionary()
            for k_parent, v_parent in quotation_details_dict.items():
                for k, v in v_parent.items():
                    if k == selected_vendor_ids[4]:
                        tax_ids = []
                        for tax_line in v.tax_id:
                            tax_ids.append(tax_line.id)

                        vals = {
                            'product_id': v.product_id.id,
                            'vendor_id': v.vendor_id.id,
                            'amount': v.price_unit,
                            'negotiated_rate': v.price_unit,
                            'quotation_comp_ven5_id': self.id,
                            'tax_id': [(6, 0, tax_ids)],
                        }
                    elif k != selected_vendor_ids[4]:
                        pass
                    else:
                        blank_line5 = self.env['quotation.compare.vendor5'].search(
                            [('product_id', '=', line.product_id.id), ('vendor_id', '=', None), ('quotation_comp_ven5_id', '=', self.id)])
                        if not blank_line5:
                            vals = {
                                'product_id': line.product_id.id,
                                'vendor_id': None,
                                'amount': None,
                                'negotiated_rate': None,
                                'quotation_comp_ven5_id': self.id,
                                'tax_id': None,
                            }

                quotation_compare_vendor5_list.append((0, 0, vals))
                for quotation_comp_vendor5 in self.quotation_comp_vendor5:
                    if quotation_comp_vendor5.id not in quotation_compare_vendor5_list:
                        quotation_compare_vendor5_list.append(
                            (2, quotation_comp_vendor5.id))
                self.update(
                    {'quotation_comp_vendor5': quotation_compare_vendor5_list})

            quotation_compare_vendor6_list = []
            vals = {}
            quotation_details_dict = self.compute_quotation_details_dictionary()
            for k_parent, v_parent in quotation_details_dict.items():
                for k, v in v_parent.items():
                    if k == selected_vendor_ids[5]:
                        tax_ids = []
                        for tax_line in v.tax_id:
                            tax_ids.append(tax_line.id)

                        vals = {
                            'product_id': v.product_id.id,
                            'vendor_id': v.vendor_id.id,
                            'amount': v.price_unit,
                            'negotiated_rate': v.price_unit,
                            'quotation_comp_ven6_id': self.id,
                            'tax_id': [(6, 0, tax_ids)],
                        }
                    elif k != selected_vendor_ids[5]:
                        pass
                    else:
                        blank_line6 = self.env['quotation.compare.vendor6'].search(
                            [('product_id', '=', line.product_id.id), ('vendor_id', '=', None), ('quotation_comp_ven6_id', '=', self.id)])
                        if not blank_line6:
                            vals = {
                                'product_id': line.product_id.id,
                                'vendor_id': None,
                                'amount': None,
                                'negotiated_rate': None,
                                'quotation_comp_ven6_id': self.id,
                                'tax_id': None,
                            }

                quotation_compare_vendor6_list.append((0, 0, vals))
                for quotation_comp_vendor6 in self.quotation_comp_vendor6:
                    if quotation_comp_vendor6.id not in quotation_compare_vendor6_list:
                        quotation_compare_vendor6_list.append(
                            (2, quotation_comp_vendor6.id))
                self.update(
                    {'quotation_comp_vendor6': quotation_compare_vendor6_list})

        except IndexError:
            pass

    @api.depends('quotation_comp_vendor1.negotiated_rate', 'quotation_comp_vendor1.amount', 'quotation_comp_particular.product_qty')
    @api.onchange('quotation_comp_vendor1', 'quotation_comp_particular')
    def compute_quotation_comp_tax1(self):
        qty_list = []
        for particular in self.quotation_comp_particular:
            qty_list.append(particular.product_qty)
        index = 0
        for vendor in self.quotation_comp_vendor1:
            vendor.write({'amount': qty_list[index] * vendor.negotiated_rate})
            index += 1

    @api.depends('quotation_comp_vendor2.negotiated_rate', 'quotation_comp_vendor2.amount', 'quotation_comp_particular.product_qty')
    @api.onchange('quotation_comp_vendor2', 'quotation_comp_particular')
    def compute_quotation_comp_tax2(self):
        qty_list = []
        for particular in self.quotation_comp_particular:
            qty_list.append(particular.product_qty)
        index = 0
        for vendor in self.quotation_comp_vendor2:
            vendor.write({'amount': qty_list[index] * vendor.negotiated_rate})
            index += 1

    @api.depends('quotation_comp_vendor3.negotiated_rate', 'quotation_comp_vendor3.amount', 'quotation_comp_particular.product_qty')
    @api.onchange('quotation_comp_vendor3', 'quotation_comp_particular')
    def compute_quotation_comp_tax3(self):
        qty_list = []
        for particular in self.quotation_comp_particular:
            qty_list.append(particular.product_qty)
        index = 0
        for vendor in self.quotation_comp_vendor3:
            vendor.write({'amount': qty_list[index] * vendor.negotiated_rate})
            index += 1

    @api.depends('quotation_comp_vendor4.negotiated_rate', 'quotation_comp_vendor4.amount', 'quotation_comp_particular.product_qty')
    @api.onchange('quotation_comp_vendor4', 'quotation_comp_particular')
    def compute_quotation_comp_tax4(self):
        qty_list = []
        for particular in self.quotation_comp_particular:
            qty_list.append(particular.product_qty)
        index = 0
        for vendor in self.quotation_comp_vendor4:
            vendor.write({'amount': qty_list[index] * vendor.negotiated_rate})
            index += 1

    @api.depends('quotation_comp_vendor5.negotiated_rate', 'quotation_comp_vendor5.amount', 'quotation_comp_particular.product_qty')
    @api.onchange('quotation_comp_vendor5', 'quotation_comp_particular')
    def compute_quotation_comp_tax5(self):
        qty_list = []
        for particular in self.quotation_comp_particular:
            qty_list.append(particular.product_qty)
        index = 0
        for vendor in self.quotation_comp_vendor5:
            vendor.write({'amount': qty_list[index] * vendor.negotiated_rate})
            index += 1

    @api.depends('quotation_comp_vendor6.negotiated_rate', 'quotation_comp_vendor6.amount', 'quotation_comp_particular.product_qty')
    @api.onchange('quotation_comp_vendor6', 'quotation_comp_particular')
    def compute_quotation_comp_tax6(self):
        qty_list = []
        for particular in self.quotation_comp_particular:
            qty_list.append(particular.product_qty)
        index = 0
        for vendor in self.quotation_comp_vendor6:
            vendor.write({'amount': qty_list[index] * vendor.negotiated_rate})
            index += 1


class MaterialList(models.Model):
    _name = 'material.list'
    _description = 'Material List'

    quotation_comp_mat_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    material_id = fields.Many2one('product.product', 'Material')
    is_material = fields.Boolean('Use Material')


class SupplierList(models.Model):
    _name = "supplier.list"
    _description = 'Supplier List'

    quotation_comp_sup_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    is_vendor = fields.Boolean('Use Vendor')


class QuotationDetails(models.Model):
    _name = "quotation.details"
    _description = 'Quotation Details'

    name = fields.Char("Quotation No")
    date = fields.Date('Date')
    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit')
    price_unit = fields.Float('Rate')
    negotiated_rate = fields.Float('Negotiated Rate')
    price_subtotal = fields.Float('Subtotal')
    is_use = fields.Boolean('Use')
    tax_id = fields.Many2many(
        'account.tax', 'quotation_detail_tax_rel', 'tax_id', 'quot_detail_id', string='Taxes')
    tax_percent = fields.Float('Tax Percent')
    tax = fields.Float('Total Tax')
    quotation_comp_detail_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_details_ = fields.One2many(
        'quotation.compare.particular', 'quotation_comp_pert_detail_id', string='Quotation Details Line')
    quotation_details_ven1 = fields.One2many(
        'quotation.compare.vendor1', 'quotation_comp_ven1_detail_id', string='Quotation Details Vendor1')
    quotation_details_ven2 = fields.One2many(
        'quotation.compare.vendor2', 'quotation_comp_ven2_detail_id', string='Quotation Details Vendor2')
    quotation_details_ven3 = fields.One2many(
        'quotation.compare.vendor3', 'quotation_comp_ven3_detail_id', string='Quotation Details Vendor3')
    quotation_details_ven4 = fields.One2many(
        'quotation.compare.vendor4', 'quotation_comp_ven4_detail_id', string='Quotation Details Vendor4')
    quotation_details_ven5 = fields.One2many(
        'quotation.compare.vendor5', 'quotation_comp_ven5_detail_id', string='Quotation Details Vendor5')
    quotation_details_ven6 = fields.One2many(
        'quotation.compare.vendor6', 'quotation_comp_ven6_detail_id', string='Quotation Details Vendor6')
    quotation_tax_per = fields.One2many(
        'tax.particular', 'quotation_comp_taxper_detail_id', string='Quotation Particular Tax')
    quotation_tax1_detail_per = fields.One2many(
        'tax.details.vendor1', 'quotation_comp_tax1_detail_id', string='Quotation Detail Tax1')
    quotation_tax2_detail_per = fields.One2many(
        'tax.details.vendor2', 'quotation_comp_tax2_detail_id', string='Quotation Detail Tax2')
    quotation_tax3_detail_per = fields.One2many(
        'tax.details.vendor3', 'quotation_comp_tax3_detail_id', string='Quotation Detail Tax3')
    quotation_tax4_detail_per = fields.One2many(
        'tax.details.vendor4', 'quotation_comp_tax4_detail_id', string='Quotation Detail Tax4')
    quotation_tax5_detail_per = fields.One2many(
        'tax.details.vendor5', 'quotation_comp_tax5_detail_id', string='Quotation Detail Tax5')
    quotation_tax6_detail_per = fields.One2many(
        'tax.details.vendor6', 'quotation_comp_tax6_detail_id', string='Quotation Detail Tax6')


class QuotationCompareParticular(models.Model):
    _name = 'quotation.compare.particular'
    _description = 'Quotation Compare Particular'

    product_id = fields.Many2one('product.product', 'Particular')
    price_expt = fields.Float('Expected Rate')
    product_qty = fields.Float('Quantity', default=1)
    product_uom = fields.Many2one('uom.uom', string='Unit')
    quotation_comp_pert_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_pert_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')
    is_approve = fields.Boolean('Select')


class QuotationCompareVendor1(models.Model):
    _name = "quotation.compare.vendor1"
    _description = 'Quotation Compare Vendor 1'

    product_id = fields.Many2one('product.product', 'Particular')
    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    negotiated_rate = fields.Float('Nego.Rate')
    tax_id = fields.Many2many(
        'account.tax', 'quotation_com1_tax_rel', 'tax_id', 'quot_comp1_id', string='Taxes')
    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')
    quotation_comp_ven1_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_ven1_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')
    is_approve = fields.Boolean('Approve')

    def approve_vendor1(self):
        #         for i in self:
        self.update({'is_approve': 1})

    def cancel_vendor1(self):
        self.update({'is_approve': 0})


class QuotationCompareVendor2(models.Model):
    _name = "quotation.compare.vendor2"
    _description = 'Quotation Compare Vendor 2 '

    product_id = fields.Many2one('product.product', 'Particular')
    tax_id = fields.Many2many(
        'account.tax', 'quotation_comp2_tax_rel', 'tax_id', 'quot_comp2_id', string='Taxes')
    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    negotiated_rate = fields.Float('Nego.Rate')
    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')
    quotation_comp_ven2_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_ven2_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')
    is_approve = fields.Boolean('Approve')

    def approve_vendor2(self):
        #         for i in self:
        self.update({'is_approve': 1})

    def cancel_vendor2(self):
        self.update({'is_approve': 0})


class QuotationCompareVendor3(models.Model):
    _name = "quotation.compare.vendor3"
    _description = 'Quotation Compare Vendor 3'

    product_id = fields.Many2one('product.product', 'Particular')
    tax_id = fields.Many2many(
        'account.tax', 'quotation_comp3_tax_rel', 'tax_id', 'quot_comp3_id', string='Taxes')
    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    negotiated_rate = fields.Float('Nego.Rate')
    amount = fields.Float('Amount')
    quotation_comp_ven3_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_ven3_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')
    is_approve = fields.Boolean('Approve')

    def approve_vendor3(self):
        #         for i in self:
        self.update({'is_approve': 1})

    def cancel_vendor3(self):
        self.update({'is_approve': 0})


class QuotationCompareVendor4(models.Model):
    _name = "quotation.compare.vendor4"
    _description = 'Quotation Compare Vendor 4'

    product_id = fields.Many2one('product.product', 'Particular')
    tax_id = fields.Many2many(
        'account.tax', 'quotation_comp4_tax_rel', 'tax_id', 'quot_comp4_id', string='Taxes')
    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    negotiated_rate = fields.Float('Nego.Rate')
    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')
    quotation_comp_ven4_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_ven4_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')
    is_approve = fields.Boolean('Approve')

    def approve_vendor4(self):
        self.update({'is_approve': 1})

    def cancel_vendor4(self):
        self.update({'is_approve': 0})


class QuotationCompareVendor5(models.Model):
    _name = "quotation.compare.vendor5"
    _description = 'Quotation Compare Vendor 5'

    product_id = fields.Many2one('product.product', 'Particular')
    tax_id = fields.Many2many(
        'account.tax', 'quotation_comp5_tax_rel', 'tax_id', 'quot_comp5_id', string='Taxes')
    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    negotiated_rate = fields.Float('Nego.Rate')
    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')
    quotation_comp_ven5_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_ven5_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')
    is_approve = fields.Boolean('Approve')

    def approve_vendor5(self):
        self.update({'is_approve': 1})

    def cancel_vendor5(self):
        self.update({'is_approve': 0})


class QuotationCompareVendor6(models.Model):
    _name = "quotation.compare.vendor6"
    _description = 'Quotation Compare Vendor 6'

    product_id = fields.Many2one('product.product', 'Particular')
    tax_id = fields.Many2many(
        'account.tax', 'quotation_comp6_tax_rel', 'tax_id', 'quot_comp6_id', string='Taxes')
    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    negotiated_rate = fields.Float('Nego.Rate')
    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')
    quotation_comp_ven6_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_ven6_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')
    is_approve = fields.Boolean('Approve')

    def approve_vendor6(self):
        self.update({'is_approve': 1})

    def cancel_vendor6(self):
        self.update({'is_approve': 0})


class TaxParticular(models.Model):
    _name = "tax.particular"
    _description = 'Tax Particular'

    product_id = fields.Many2one('product.product', 'product')
    quotation_comp_taxper_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_taxper_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')


class TaxDetailsVendor1(models.Model):
    _name = "tax.details.vendor1"
    _description = 'Tax Details Vendor 1'

    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    product_id = fields.Many2one('product.product', 'product')
    tax_id = fields.Many2many(
        'account.tax', 'quotation_comp1_tax_rel', 'tax_id', 'quot_comp1_id', string='Taxes')
    tax = fields.Float('Tax')
    quotation_comp_tax1_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_tax1_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')


class TaxDetailsVendor2(models.Model):
    _name = "tax.details.vendor2"
    _description = 'Tax Details Vendor 2'

    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    product_id = fields.Many2one('product.product', 'product')
    tax_id = fields.Many2many(
        'account.tax', 'tax_detail2_tax_rel', 'tax_id', 'tax_detail_vendor2_id', string='Taxes')
    tax = fields.Float('Tax')
    quotation_comp_tax2_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_tax2_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')


class TaxDetailsVendor3(models.Model):
    _name = "tax.details.vendor3"
    _description = 'Tax Details Vendor 3'

    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    product_id = fields.Many2one('product.product', 'product')
    tax_id = fields.Many2many(
        'account.tax', 'tax_detail3_tax_rel', 'tax_id', 'tax_detail_vendor3_id', string='Taxes')
    tax = fields.Float('Tax')
    quotation_comp_tax3_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_tax3_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')


class TaxDetailsVendor4(models.Model):
    _name = "tax.details.vendor4"
    _description = 'Tax Details Vendor 4'

    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    product_id = fields.Many2one('product.product', 'product')
    tax_id = fields.Many2many(
        'account.tax', 'tax_detail4_tax_rel', 'tax_id', 'tax_detail_vendor4_id', string='Taxes')
    tax = fields.Float('Tax')
    quotation_comp_tax4_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_tax4_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')


class TaxDetailsVendor5(models.Model):
    _name = "tax.details.vendor5"
    _description = 'Tax Details Vendor 5'

    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    product_id = fields.Many2one('product.product', 'product')
    tax_id = fields.Many2many(
        'account.tax', 'tax_detail5_tax_rel', 'tax_id', 'tax_detail_vendor5_id', string='Taxes')
    tax = fields.Float('Tax')
    quotation_comp_tax5_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_tax5_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')


class TaxDetailsVendor6(models.Model):
    _name = "tax.details.vendor6"
    _description = 'Tax Details Vendor 6'

    vendor_id = fields.Many2one(
        'res.partner', 'Vendor', domain=[('supplier', '=', True)])
    product_id = fields.Many2one('product.product', 'product')
    tax_id = fields.Many2many(
        'account.tax', 'tax_detail6_tax_rel', 'tax_id', 'tax_detail_vendor6_id', string='Taxes')
    tax = fields.Float('Tax')
    quotation_comp_tax6_id = fields.Many2one(
        'quotation.comparison', 'Quotation')
    quotation_comp_tax6_detail_id = fields.Many2one(
        'quotation.details', string='Quotation details', ondelete='cascade')
