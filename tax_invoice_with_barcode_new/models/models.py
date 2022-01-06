# -*- coding: utf-8 -*-
import qrcode
import base64
from io import BytesIO
from datetime import datetime,date

from odoo import models, fields, api



class Account_move(models.Model):
    _inherit = 'account.move'

    cbs_servuces_taxable = fields.Float(string="", required=False, )
    total_taxes = fields.Float(string="", required=False, compute='get_total_taxes')
    total_discount = fields.Float(string="Total Discount",  required=False,compute='get_total_discount' )
    # warehouse_name = fields.Char(string="Warehouse Name", required=False,compute='get_warehouse_name' )
    company_seal = fields.Html(string="ختم الشركة",  )
    project = fields.Char(string="Project", required=False, )
    contract_no = fields.Char(string="Contract No", required=False, )

    # @api.depends('invoice_line_ids')
    # def get_warehouse_name(self):
    #     for rec in self:
    #         rec.warehouse_name = ''
    #         invoice_line_sales = rec.invoice_line_ids.filtered(lambda x:x.sale_line_ids)
    #         if invoice_line_sales:
    #             rec.warehouse_name = invoice_line_sales[0].sale_line_ids[0].order_id.warehouse_id.display_name

    @api.depends()
    def get_total_discount(self):
        for rec in self:
            rec.total_discount = sum(rec.invoice_line_ids.mapped('discount_amount'))

    # def create_qr_code(self, url):
    #     # qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=2, )
    #     qr = qrcode.QRCode(version=5, error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=200, border=1)
    #     qr.add_data(url.encode('utf-8'))
    #     qr.make(fit=True)
    #     # img = qr.make_image(fill_color="black", back_color="white")
    #     img = qr.make_image()
    #     temp = BytesIO()
    #     img.save(temp, format="PNG")
    #     qr_img = base64.b64encode(temp.getvalue())
    #     return qr_img

    qr_code_image = fields.Char("QR Code", copy=False, readonly=1,compute='generate_qr_code')

    # def generate_qr_code(self):
    #     for rec in self:
    #         qr_info = self.env.company.name + '/' + self.env.company.vat + "\n"
    #         qr_info += str(rec.invoice_date) + "\n"
    #         qr_info += "VAT: " + str(round(rec.total_taxes, 2)) + "\n"
    #         qr_info += "TOT: " + str(round(rec.amount_total, 2))
    #         rec.qr_code_image = rec.sudo().create_qr_code(qr_info)
    #         return rec.qr_code_image

    def get_InvDateTime(self):
        for rec in self:
            date = False
            if rec.invoice_date:
                timezone = self._context.get('tz') or self.env.user.tz or 'UTC'
                self_tz = self.with_context(tz=timezone)
                mydatetime = datetime.combine(rec.invoice_date, datetime.now().time())
                date = fields.Datetime.context_timestamp(self_tz, mydatetime)
                date = date.strftime("%Y-%m-%d %H:%M:%S")
                date = datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S")
            return date

    def generate_qr_code(self):
        """ Generate the qr code for Saudi e-invoicing. Specs are available at the following link at page 23
            https://zatca.gov.sa/ar/E-Invoicing/SystemsDevelopers/Documents/20210528_ZATCA_Electronic_Invoice_Security_Features_Implementation_Standards_vShared.pdf
        """

        def get_qr_encoding(tag, field):
            value = field.encode('UTF-8')
            tag = tag.to_bytes(length=1, byteorder='big')
            length = len(value).to_bytes(length=1, byteorder='big')
            return tag + length + value

        for rec in self:
            qr_code_str = ''
            date = rec.get_InvDateTime()
            if rec.company_id and date and rec.company_id.vat:
                seller_name_enc = get_qr_encoding(1, rec.company_id.display_name)
                company_vat_enc = get_qr_encoding(2, rec.company_id.vat)
                # time_sa = fields.Datetime.context_timestamp(self.with_context(tz='Asia/Riyadh'),
                #                                             rec.get_invDate_currentTime())
                timestamp_enc = get_qr_encoding(3, date.isoformat())
                invoice_total_enc = get_qr_encoding(4, str(rec.amount_total))
                total_vat_enc = get_qr_encoding(5, str(rec.total_taxes))
                str_to_encode = seller_name_enc + company_vat_enc + timestamp_enc + invoice_total_enc + total_vat_enc
                qr_code_str = base64.b64encode(str_to_encode).decode('UTF-8')
            rec.qr_code_image = qr_code_str



    # @api.depends('invoice_line_ids')
    # def get_cbs_servuces_taxable(self):
    #      self.total_exclude_vat = sum(self.invoice_line_ids.filtered(lambda x:x.tax_ids).mapped('price_subtotal'))



    @api.depends('invoice_line_ids')
    def get_total_taxes(self):
        for rec in self:
            total_with_out_tax = sum(rec.invoice_line_ids.mapped('price_subtotal'))
            total_with_tax = sum(rec.invoice_line_ids.mapped('price_total'))
            rec.total_taxes = total_with_tax - total_with_out_tax


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    tax_amount = fields.Float(string="Tax Amount", required=False, compute='get_tax_amount')
    discount_amount = fields.Float('discount amount',compute='get_discount_amount')
    price_include = fields.Boolean(string='Included in Price', default=False,
                                   help="Check this if the price you use on the product and invoices includes this tax",
                                   compute='check_price_include', store=True)
    price_before_discount = fields.Float(string="",compute='get_price_before_discount',  required=False, )
    # prices_with_vat_include = fields.Float(string='price with Tax',compute='get_prices_with_vat_include')
    # taxable_amount = fields.Float(string="Taxable Amount",  required=False,compute='get_taxable_amount' )

    @api.depends('tax_ids')
    def check_price_include(self):
        for rec in self:
            rec.price_include = False
            if rec.tax_ids:
                if rec.tax_ids[0].price_include:
                    rec.price_include = True


    @api.depends('product_id','discount','price_unit','quantity')
    def get_discount_amount(self):
        for rec in self:
            if rec.price_include:
                rec.discount_amount = rec.price_subtotal * rec.discount / 100
            else:
                rec.discount_amount = (rec.price_unit * rec.quantity) * rec.discount / 100

    @api.depends()
    def get_price_before_discount(self):
        for rec in self:
            if rec.quantity != 0:
                rec.price_before_discount = rec.price_subtotal / rec.quantity

    @api.depends('price_subtotal', 'price_total')
    def get_tax_amount(self):
        for rec in self:
            rec.tax_amount = 0.0
            if rec.move_id.move_type == 'out_invoice':
                rec.tax_amount = round(rec.price_total - rec.price_subtotal, 2)
            if rec.move_id.move_type == 'out_refund':
                rec.tax_amount = round((rec.price_total - rec.price_subtotal), 2)




