from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.fields import Many2one
from odoo.exceptions import UserError


class Procurement(models.TransientModel):
    _name = 'purchase.procurement'
    _description = 'Procurement'

    project_id = Many2one('project.project', 'Project Name', required=False)
    sub_project = fields.Many2one('sub.project', 'Sub Project')
    project_wbs = Many2one('project.task', domain=[
                           ('is_wbs', '=', True), ('is_task', '=', False)], required=False)

    sub_project = fields.Many2one('sub.project', 'Sub Project')

    material_id = Many2one('product.product', 'Material Name')
    material = fields.Selection([('All Material', 'All Material'), ('Show All Material from project', 'Show All Material from project'),
                                 ('Single Material', 'single Material')])
    material_selection = fields.Selection([('all', 'All Material'), ('from_single_project', 'Show All Material from project'),
                                           ('single', 'single Material')], default='from_single_project')
    from_date = fields.Date(
        'From  Date', default=str(datetime.now() + timedelta(days=-7)), required=True)
    to_date = fields.Date(
        'To Date', default=str(fields.date.today()), required=True)
    procurement_type = fields.Selection([('New Purchase from Supplier', 'New Purchase from Supplier'),
                                         ('Cash Purchase ', 'Cash Purchase '),
                                         ('IST from other sites', 'IST from other sites'), ], 'Procurement Type')
    project_task_id = fields.Many2one('project.task', 'Project/Store')
    procurement_line_ids = fields.One2many(
        'procurement.line', 'procurement_id', string='Requisition Order')
    warehouse_id = fields.Many2one(
        'stock.warehouse', 'procurement Type', required=True)
    select_all = fields.Boolean('Select All', Default=False)

    
    @api.onchange('warehouse_id')
    def warehouse_id_method(self):
        if self.warehouse_id:
            # setting warehouse in Lines
            warehouse__lst = []
            for warehouse_line_id in self.procurement_line_ids:
                if warehouse_line_id.is_select:
                    warehouse_line_id.warehouse_id = self.warehouse_id

#     @api.onchange('project_id')
#     def project_id_onchange(self):
#         # return required domain,ie.wbs of only selected project and materials
#         # of selected wbs
#         material_list = []
#         project_wbs_lst = []
#         if self.project_id:
#             project_ids = self.env['project.task'].search(
#                 [('project_id', '=', self.project_id.id)])
#             for i in project_ids:
#                 project_wbs_lst.append(i.name)
#         if self.project_wbs:
#             project_task_obj = self.env['project.task'].search(
#                 [('project_id', '=', self.project_id.id), ('name', '=', self.project_wbs.name)])
#             for line in project_task_obj.material_estimate_line:
#                 material_list.append(line.name.id)
#         return {'domain': {'project_wbs': [('name', 'in', project_wbs_lst)], 'material_id': [('id', 'in', material_list)]}}

    
    @api.onchange('select_all')
    def is_use_onchange(self):
        for line in self.procurement_line_ids:
            line.update({'is_select': self.select_all})

    @api.onchange('procurement_line_ids')
    def procurement_line_ids_method(self):
        for i in self.procurement_line_ids:
            if not i.is_select:
                self.select_all = False

    def check_select_all(self):
        for line in self.procurement_line_ids:
            if not line.is_select:
                self.select_all = False
                break

    
    def compute_procurements_lines(self):
        self.procurement_line_ids.unlink()
        if self.from_date > self.to_date:
            raise UserError("From Date should be lesser than To Date")
        self.ensure_one()
        self.name = "New name"
        if self.material_selection == 'all':
            req_obj_list = []
            self.project_id = self.project_wbs = self.material_id = None
            req_obj = self.env['purchase.requisition'].search([])
            for req_obj in req_obj:
                vals = {
                    'material_id': req_obj.material_id.id,
                    'quantity': req_obj.quantity,
                    'unit': req_obj.unit.id,
                    'rate': req_obj.rate,
                    'task_id': req_obj.task_id.id,
                    'group_id': req_obj.group_id.id,
                    'requisition_no': req_obj.name,
                    'warehouse_id': self.warehouse_id,
                }
                req_obj_list.append((0, 0, vals))
            self.update({'procurement_line_ids': req_obj_list})
        else:
            vals = {}
            requisition_list = []
            domain = []
            domain.append(('requisition_date', '>=', self.from_date))
            domain.append(('requisition_date', '<=', self.to_date))
            #             domain.append(('name','like','Req'))
            if self.project_id:
                domain.append(('project_id', '=', self.project_id.id))
            if self.sub_project:
                domain.append(('sub_project', '=', self.sub_project.id))
            if self.project_wbs:
                domain.append(('project_wbs', '=', self.project_wbs.id))
            if self.material_id:
                domain.append(('material_id', '=', self.material_id.id))

            requisition_line_obj = self.env[
                'purchase.requisition'].search(domain)
            for req_lines in requisition_line_obj:
                vals = {
                    'material_id': req_lines.material_id.id,
                    'quantity': req_lines.quantity,
                    'unit': req_lines.unit.id,
                    'rate': req_lines.rate,
                    'task_id': req_lines.task_id.id,
                    'group_id': req_lines.group_id.id,
                    'requisition_no': req_lines.name,
                    'warehouse_id': self.warehouse_id,
                }
                requisition_list.append((0, 0, vals))
            self.update({'procurement_line_ids': requisition_list})
        return {
            'context': self.env.context,
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.procurement',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    
    def save_method(self):
        # set procurement type in requisition line
        requisition_no_list = []
        for procure_lines in self.procurement_line_ids:
            if procure_lines.is_select == True:
                requisition_no_list.append(procure_lines.requisition_no)
                resulted_req_lines = self.env['purchase.requisition'].search(
                    [('name', '=', procure_lines.requisition_no)])
                for i in resulted_req_lines:
                    i.warehouse_id = self.warehouse_id.name


class ProcurementLines(models.TransientModel):
    _name = 'procurement.line'
    _description = 'Procurement Lines'

    is_select = fields.Boolean('Select', Default=False)
    name = fields.Many2one('project.task', 'project')
    group_id = fields.Many2one('project.task', 'Group')
    task_id = fields.Many2one('project.task', 'Task')

    requisition_no = fields.Char('Requisition No')
    material_id = fields.Many2one('product.product', 'Material')
    requisition_date = fields.Date('Date', default=fields.date.today())
    requirement_date = fields.Date('Requirement Date')
    quantity = fields.Integer('Quantity')
    specification = fields.Char('Specification')
    remark = fields.Char('Remark')
    total_approved_qty = fields.Float('Approved Qty', readonly=True)
    total_ordered_qty = fields.Float('Ordered Qty', readonly=True)
    balance_qty = fields.Float('Balance Qty')
    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], 'Status')
    priority = fields.Selection([('high', 'High'), ('low', 'Low')], 'Priority')
    brand_id = fields.Many2one('brand.brand', 'Brand')
    requisition_type = fields.Selection(
        [('estimated', 'Estimated'), ('non_estimated', 'Non Estimated')], 'Type')
    order_id = fields.Many2one('requisition.order', 'order_line_id')
    unit = fields.Many2one('uom.uom', 'UOM')
    rate = fields.Float('Rate')
    procurement_id = fields.Many2one('purchase.procurement')
    procurement_type = fields.Selection([('New Purchase from Supplier', 'New Purchase from Supplier'),
                                         ('Cash Purchase ', 'Cash Purchase '),
                                         ('IST from other sites', 'IST from other sites'), ], 'Procurement Type')
    warehouse_id = fields.Many2one('stock.warehouse', 'Project Store')
