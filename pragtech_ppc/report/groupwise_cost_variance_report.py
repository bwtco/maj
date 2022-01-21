## -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# from odoo.report import report_sxw


# class groupwise_cost_variance(report_sxw.rml_parse):
#     def __init__(self, cr, uid, name, context):
#         super(groupwise_cost_variance, self).__init__(cr, uid, name, context=context)
#         self.localcontext.update({
#             'get_project_info': self.get_project_info,
#         })

#     def get_project_info(self):
#         return True


# class groupwise_cost_variance_report(osv.AbstractModel):
#     _name = 'report.pragtech_ppc.groupwise_cost_variance_report'
#     _inherit = 'report.abstract_report'
#     _template = 'pragtech_ppc.groupwise_cost_variance_report'
#     _wrapped_report_class = groupwise_cost_variance
