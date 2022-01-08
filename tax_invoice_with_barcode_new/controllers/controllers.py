# -*- coding: utf-8 -*-
# from odoo import http


# class CbsInvoicePrint(http.Controller):
#     @http.route('/cbs_invoice_print/cbs_invoice_print/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cbs_invoice_print/cbs_invoice_print/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cbs_invoice_print.listing', {
#             'root': '/cbs_invoice_print/cbs_invoice_print',
#             'objects': http.request.env['cbs_invoice_print.cbs_invoice_print'].search([]),
#         })

#     @http.route('/cbs_invoice_print/cbs_invoice_print/objects/<model("cbs_invoice_print.cbs_invoice_print"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cbs_invoice_print.object', {
#             'object': obj
#         })
