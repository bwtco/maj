# -*- coding: utf-8 -*-
import qrcode
import base64
from io import BytesIO
from datetime import datetime,date

from odoo import models, fields, api



class Company(models.Model):
    _inherit = 'res.company'

    show_tax_invoice_header = fields.Boolean(string="Show Tax Invoice Header",  )
    invoice_tax_header_logo = fields.Binary(string="Invoice Tax Header Logo",  )
    invoice_tax_footer_logo = fields.Binary(string="Invoice Tax Footer Logo",  )
