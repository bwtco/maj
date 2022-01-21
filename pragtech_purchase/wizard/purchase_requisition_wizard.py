from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class PurchaseRequisitionWizard(models.TransientModel):

    _name = 'purchase.requisition.wizard'
    _description = 'Purchase Requisition Wizard'

    task_id_list = []

    def get_task_idss(self):
        self.task_id_list = []
        var = ''
        material_estimate_obj = self.env['task.material.line'].search(
            [('wbs_id', '=', self.name.id)])
        for line in material_estimate_obj:
            id = line.material_line_id.id
            var = var + ' ' + str(id)
            self.task_id_list.append(id)
        self.group_domain = self.task_id_list

    group_domain = fields.Char('Domain', default='[]')
    group_domain1 = fields.Char('Task IDs', default='[]')
    note = fields.Text(
        'Note:', default='You can only add Requisition for approved material for current vendor')
    name = fields.Many2one('project.task', 'Project WBS Name', domain=[
                           ('is_wbs', '=', True), ('is_task', '=', False)],required=True)
    project_id = fields.Many2one('project.project', 'Project',required=True)
    sub_project = fields.Many2one('sub.project', 'Sub Project' ,required=True)
    task_category = fields.Many2many(
        'task.category', 'cat_wizard_rel', 'cat_id', 'wizard_id')
    material_category = fields.Many2many(
        'product.category', 'wizard_prod_cat_rel', 'wizard_id', 'cat_id')
    material = fields.Many2one('product.product', 'Material')
    group_id = fields.Many2one('project.task', 'Task Group')
    task_id = fields.Many2one('project.task', 'Task')
    requisition_ids = fields.One2many(
        'purchase.requisition.wizard.line', 'order_id')
    to_date = fields.Date(
        'To Date', default=fields.date.today(), required=True)
    from_date = fields.Date(
        'From Date', default=str(datetime.now() + timedelta(days=-30)), required=True)
    is_use = fields.Boolean('Select All')
    task_date_type = fields.Selection([('planned', 'Planned'), ('actual', 'Actual')], string='Task Date Type',
                                      default='planned')
    date_type = fields.Selection(
        [('start_date', 'Start Date'), ('finish_date', 'Finish Date')], string='Date Type')

    is_red = fields.Boolean()  # line will red if Material rate is not approved
    task_ids_str = []

    @api.depends('group_id')
    @api.onchange('group_id')
    def group_id_onchange(self):
        task_list = []
        if self.project_id:
            wbs = self.env['project.task'].browse(self.name.id)
            for line in wbs.labour_estimate_line:
                task_list.append(line.labour_line_id.category_id.id)
        return {'domain': {'task_id': [('parent_id', '=', self.group_id.id), ('is_task', '=', True), ('project_wbs_id', '=', self.name.id)]}}

    @api.depends('category_id')
    @api.onchange('category_id')
    def task_category_onchange(self):
        return {'domain': {'task_id': [('category_id', '=', self.task_category.id), ('is_task', '=', True), ('project_wbs_id', '=', self.name.id)]}}

    def get_is_red(self, material_id, partner_id):
        price_info = self.env['product.supplierinfo'].search(
            [('product_tmpl_id', '=', material_id), ('is_active', '=', True), ('name', '=', partner_id)])
        return price_info

#     @api.multi
#     def compute_tree_labour(self):
#         return {
#             'name': _('labour tree'),
#             'context': self._context,
#             'view_type': 'tree',
#             'view_mode': 'tree',
#             'res_model': 'labour.master',
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#             'domain': [('parent_labour_id', '=', False), ('parent_group_id', '=', False)],
#         }

    @api.onchange('is_use')
    def is_use_onchange(self):
        for line in self.requisition_ids:
            line.is_use = self.is_use
#             line.write({'is_use': self.is_use})

    def write(self,vals):
        if self._context.get('project_id'):
            vals.update({'project_id':self._context.get('project_id')})

        if self._context.get('project_wbs'):
            vals.update({'name':self._context.get('project_wbs')})

        if self._context.get('sub_project'):
            vals.update({'sub_project':self._context.get('sub_project')})

        res = super(PurchaseRequisitionWizard, self).write(vals)
        return res


    @api.model
    def default_get(self, fields_list):
        purchase_order_id = self.env['purchase.order'].browse(
            self._context.get('active_id'))
        rec = models.TransientModel.default_get(self, fields_list)
        rec.update({
            'project_id': self._context.get('project_id'),
            'name': self._context.get('project_wbs'),
            'sub_project': self._context.get('sub_project'),
        })
        var = ''
        material_estimate_obj = self.env['task.material.line'].search(
            [('wbs_id', '=', self.name.id)])
        for line in material_estimate_obj:
            id = line.material_line_id.id
            var = var + ' ' + str(id)
            self.task_id_list.append(id)
        for line in self:
            line.group_domain = self.task_id_list

        return rec

    # Searching to create purchase requisition according user input

    @api.depends('project_id', 'sub_project', 'name', 'group_id', 'task_category', 'task_id', 'material_category', 'material')
    def compute_requisitions_lines(self):
        self.requisition_ids.unlink()
        # Search from different fields and add requisition depending on search
        # result
        project_task_obj = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id), ('name', '=', self.name.name), ('sub_project', '=', self.sub_project.id)])
        domain = []
        task_category = []
        material_category = []
        domain.append(('wbs_id', '=', project_task_obj.id))
        if self.task_date_type == 'planned' and self.date_type == 'start_date':
            domain.append(('planned_start_date', '>=', self.from_date))
            domain.append(('planned_start_date', '<=', self.to_date))
        if self.task_date_type == 'actual' and self.date_type == 'start_date':
            domain.append(('actual_start_date', '>=', self.from_date))
            domain.append(('actual_start_date', '<=', self.to_date))
        if self.task_date_type == 'planned' and self.date_type == 'finish_date':
            domain.append(('planned_finish_date', '>=', self.from_date))
            domain.append(('planned_finish_date', '<=', self.to_date))
        if self.task_date_type == 'actual' and self.date_type == 'finish_date':
            domain.append(('planned_finish_date', '>=', self.from_date))
            domain.append(('planned_finish_date', '<=', self.to_date))

        if self.group_id:
            domain.append(('group_id', '=', self.group_id.id))
        if self.task_id:
            domain.append(('material_line_id', '=', self.task_id.id))
        if self.material:
            domain.append(('material_id', '=', self.material.id))

        if self.task_category:
            for i in self.task_category:
                task_category.append(i.id)
            domain.append(('task_category', 'in', task_category))

        if self.material_category:
            for i in self.material_category:
                material_category.append(i.id)
            domain.append(('material_category', 'in', material_category))
        material_estimate_obj = project_task_obj.material_estimate_line.search(
            domain)

        if self.from_date > self.to_date:
            raise UserError("From Date should be lesser than To Date")
        for line in material_estimate_obj:
            if not line.material_line_id.actual_finish_date and line.balanced_requisition > 0:
                vals = {
                    'material_id': line.material_id.id,
                    'quantity': line.material_uom_qty,
                    'rate': line.material_rate,
                    'task_id': line.material_line_id.id,
                    'group_id': line.group_id.id,
                    'requisition_date': datetime.now(),
                    'task_category': line.material_line_id.category_id,
                    'unit': line.material_uom.id,
                    'me_sequence': line.name,
                    'Requisition_as_on_date': line.requisition_till_date,
                    'current_req_qty': line.material_uom_qty - line.requisition_till_date,
#                     'requisition_id': self.id,
                    'order_id': self.id,
                    'estimation_id': line.id,

                }

                abcd = self.requisition_ids.create(vals)
        view_id = self.env.ref(
            'pragtech_purchase.purchase_requisition_wizard_view').id
        return {
            'context': self.env.context,
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.requisition.wizard',
            'res_id': self.id,
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    """ Create Purchase Requisitions"""
    def create_requisitions(self):
        vals = {}
        req_ids = []
        stage = self.env['stage.master'].search([('draft', '=', True)])
        for line in self.requisition_ids:
            total_qty = 0
            domain = []
            task_category = []
            material_category = []
            domain.append(('project_wbs', '=', line.project_wbs.id))
            domain.append(('project_id', '=', line.project_id.id))
            domain.append(('sub_project', '=', line.sub_project.id))
            if line.group_id:
                domain.append(('group_id', '=', line.group_id.id))
            if line.task_id:
                domain.append(('task_id', '=', line.task_id.id))
            if line.material_id:
                domain.append(('material_id', '=', line.material_id.id))
            requisition_obj = self.env['purchase.requisition'].search(domain)
            for requisition_obj in requisition_obj:
                total_qty = total_qty + requisition_obj.quantity
            if line.is_use == True:
                vals = {
                    'project_id': line.project_id.id,
                    'sub_project': line.sub_project.id,
                    'project_wbs': line.project_wbs.id,
                    'material_id': line.material_id.id,
                    'material_category': line.material_id.categ_id.id,
                    'quantity': line.quantity,
                    'unit': line.unit.id,
                    'rate': line.rate,
                    'task_id': line.task_id.id,
                    'group_id': line.group_id.id,
                    'task_category': line.task_id.category_id,
                    'requisition_date': datetime.now(),
                    'stage_id': stage.id,
                    'estimated_qty': line.quantity,
                    'Requisition_as_on_date': line.Requisition_as_on_date,
                    'current_req_qty': line.current_req_qty,
                    'me_sequence': line.me_sequence,
                    'specification': line.specification,
                    'estimation_id': line.estimation_id.id,

                }
                res = self.env['purchase.requisition'].create(vals)

                vals = {
                    'date': datetime.now(),
                    'remark': 'Created by ' + (self.env['res.users'].browse(self._context.get('uid'))).name,
                    'model': 'purchase.requisition',
                    'res_id': res.id,
                    'author_id': self._context.get('uid'),
                    'to_stage': stage.id
                }
                re = self.env['mail.messages'].create(vals)
                req_ids.append(res.id)

                if line.current_req_qty > (line.quantity - line.Requisition_as_on_date):
                    raise UserError(
                        _('Please enter valid Requisition Quantity.'))
        view_id = self.env.ref(
            'pragtech_purchase.purchase_requisitions_tree_view').id
        context = self._context.copy()
        return {
            'name': 'Requisitions',
            # 'view_type': 'form',
            'view_mode': 'tree', 'form'
            'views': [(view_id, 'tree')],
            'res_model': 'purchase.requisition',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'domain': [('id', 'in', req_ids)],
            'context': {'project_id': self.project_id.id, 'project_wbs': self.name.id, 'sub_project': self.sub_project.id},
        }

    """search requisitions on purchase order"""

    @api.depends('project_id', 'name', 'material_category', 'material', 'to_date', 'from_date')
    def search_requisitions_on_po(self):
        self.requisition_ids.unlink()
        # Search from different fields and add requisition depending on search
        # result
        if self.from_date > self.to_date:
            raise UserError("From Date should be <= To Date")
        Purchase_order_obj = self.env['purchase.order'].browse(
            self._context.get('active_id'))
        requisition_list = []
        domain = []
        material_category = []
        # Get Approved stage from stage.master table
        stage_master_obj = self.env['stage.master'].search(
            [('approved', '=', True)], limit=1)
        domain.append(('stage_id', '=', stage_master_obj.id))
        domain.append(('project_id', '=', self.project_id.id))
        domain.append(('project_wbs', '=', self.name.id))
        domain.append(('requisition_date', '>=', self.from_date))
        domain.append(('requisition_date', '<=', self.to_date))
        if self.material:
            domain.append(('material_id', '=', self.material.id))

        if self.material_category:
            for i in self.material_category:
                material_category.append(i.id)
            domain.append(('material_category', 'in', material_category))
        purchase_requisition_obj = self.env[
            'purchase.requisition'].search(domain)
        for line in purchase_requisition_obj:

            product_supplier_obj = self.env['product.supplierinfo'].search(
                [('product_name', '=', line.material_id.name), ('is_active', '=', True), ('name', '=', Purchase_order_obj.partner_id.id)])
            if(line.current_req_qty - line.total_ordered_qty) > 0:
                price_info = self.get_is_red(
                    line.material_id.id, Purchase_order_obj.partner_id.id)
                if product_supplier_obj:
                    vals = {
                        'project_id': self.project_id.id,
                        'project_wbs': self.name.id,
                        'requisition_name': line.id,
                        'material_id': line.material_id.id,
                        'quantity': line.quantity,
                        'unit': line.unit.id,
                        'task_id': line.task_id.id,
                        'group_id': line.group_id.id,
                        'requisition_qty': line.current_req_qty,
                        'total_ordered_qty': line.total_ordered_qty,
                        'current_order_qty': line.current_req_qty - line.total_ordered_qty,
                        'me_sequence': line.me_sequence,
                        'specification': line.specification
                    }
                else:
                    vals = {
                        'project_id': self.project_id.id,
                        'project_wbs': self.name.id,
                        'requisition_name': line.id,
                        'material_id': line.material_id.id,
                        'quantity': line.quantity,
                        'unit': line.unit.id,
                        'task_id': line.task_id.id,
                        'group_id': line.group_id.id,
                        'requisition_qty': line.current_req_qty,
                        'total_ordered_qty': line.total_ordered_qty,
                        'current_order_qty': 0,
                        'me_sequence': line.me_sequence,
                        'specification': line.specification
                    }
                if price_info:
                    vals.update({'rate': price_info.price, 'is_red': False})
                else:
                    vals.update({'rate': line.rate, 'is_red': True})
                requisition_list.append((0, 0, vals))
        self.update({'requisition_ids': requisition_list})

        view_id = self.env.ref(
            'pragtech_purchase.requisition_wizard_for_po').id
        return {
            'name': 'Add Requisition',
            'context': self.env.context,
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.requisition.wizard',
            'res_id': self.id,
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    """ Add Requisitions on PO Requisition (Above Purchase Order Lines)"""

    def add_requisitions(self):
        # print("add_requisitions----------------",self)
        po_requisition_list = []
        Purchase_order_obj = self.env['purchase.order'].browse(
            self._context.get('active_id'))
        po_requisition_line_obj = self.env['po.requisition'].search(
            [('order_id', '=', self._context.get('active_id'))])
        old_po_requisition_lines = [
            line.requisition_id for line in po_requisition_line_obj]
        vals = {}
        for line in self.requisition_ids:
            if line.is_use:
                if line.current_order_qty > (line.requisition_qty - line.total_ordered_qty):
                    raise UserError(
                        _('Order quantity must be less than requisition quantity.'))
                if line.current_order_qty == 0:
                    raise UserError(_('Please enter valid Requisition Quantity'))
                if line.is_red and line.is_use == False:
                    raise UserError('You can only add Requisition for approved material for current vendor')
                if line.requisition_name not in old_po_requisition_lines and line.current_order_qty > 0 and line.current_order_qty <= (line.requisition_qty - line.total_ordered_qty):

                    vals = {
                        'project_id': self.project_id.id,
                        'project_wbs': self.name.id,
                        'sub_project': self.sub_project.id,
                        'material_id': line.material_id.id,
                        'material_category': line.material_id.categ_id.id,
                        'quantity': line.quantity,
                        'unit': line.unit.id,
                        'rate': line.rate,
                        'task_id': line.task_id.id,
                        'group_id': line.group_id.id,
                        'current_req_qty': (line.current_req_qty),
                        'requisition_qty': line.requisition_qty,
                        'total_ordered_qty': line.total_ordered_qty,
                        'current_order_qty': line.current_order_qty,
                        'me_sequence': line.me_sequence,
                        'order_id': self._context.get('active_id'),
                        'requisition_id': line.requisition_name.id,
                        'specification': line.specification,
                    }
                    # and Purchase_order_obj.order_id.state=='shipment'
                    if Purchase_order_obj.stage_id.approved == True:
                        stage_master_obj = self.env['stage.master'].search(
                            [('amend_and_draft', '=', True)], limit=1)
                        Purchase_order_obj.stage_id = stage_master_obj.id
                        Purchase_order_obj.flag = False
                        Purchase_order_obj.state = 'draft'
                    self.env['po.requisition'].create(vals)
        Purchase_order_obj.compute_po_lines(Purchase_order_obj, self.name, self.project_id)


class purchaseRequisitionWizardLine(models.TransientModel):
    _name = 'purchase.requisition.wizard.line'
    _description = 'Purchase Requisition Wizard Line'

    def change_state(self):
        view_id = self.env.ref(
            'pragtech_purchase.approval_wizard_form_view_purchase').id
        return {

            'type': 'ir.actions.act_window',
            'key2': 'client_action_multi',
            'res_model': "approval.wizard",
            'multi': "True",
            'target': 'new',
            'views': [[view_id, 'form']],
        }
    is_red = fields.Boolean()  # line will red if Material rate is not approved
    is_use = fields.Boolean('')
    name = fields.Char('Requisition No')
    group_id = fields.Many2one('project.task', 'Task Group')
    task_id = fields.Many2one('project.task', 'Task')
    flag = fields.Boolean('Flag', default=False)
    material_id = fields.Many2one('product.product', 'Material')
    requisition_date = fields.Date(
        'Date', default=fields.date.today(), required=True)
    requirement_date = fields.Date('Requirement Date')
    procurement_date = fields.Date('Procurement Date')
    quantity = fields.Float('Estimated Quantity')
    specification = fields.Char('Specification')
    remark = fields.Char('Remark')
    # previous quantity fields
    total_approved_qty = fields.Float('Approved Qty', readonly=True)
    balance_qty = fields.Float('Balance Qty')

    total_ordered_qty = fields.Float('Ordered Qty')
    requisition_qty = fields.Float('Requisition Qty')
    current_order_qty = fields.Float('Current Order Qty')

    # latest as suggested on 26/12/16 quantity fields
    estimated_qty = fields.Float('Estimated Qty')
    Requisition_as_on_date = fields.Float('Requisition as on date')
    # , compute='get_current_req_qty'
    current_req_qty = fields.Float('Current requisition Qty', readonly=False)

    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], 'Status')
    priority = fields.Selection([('high', 'High'), ('low', 'Low')], 'Priority')
    brand_id = fields.Many2one('brand.brand', 'Brand')
    requisition_type = fields.Selection(
        [('estimated', 'Estimated'), ('non_estimated', 'Non Estimated')], 'Type')
    order_id = fields.Many2one(
        'purchase.requisition.wizard', 'requisition_ids')
    unit = fields.Many2one('uom.uom', 'UOM', required=True)
    rate = fields.Float('Rate')
    procurement_type = fields.Selection([('New Purchase from Supplier', 'New Purchase from Supplier'),
                                         ('Cash Purchase ', 'Cash Purchase '),
                                         ('IST from other sites', 'IST from other sites'), ], "Procurement Type")
    warehouse_id = fields.Char('Procurement Type', readonly=True)
#     purchase_ids = fields.Many2many('purchase.order', string='Purchase Order')
    #     requisition_fulfill = fields.Boolean('Req fulfill')
    stage_id = fields.Many2one(
        'transaction.stage', domain=[('model', '=', 'requisition.order.line')])
    project_wbs = fields.Many2one(
        'project.task', related='order_id.name', store=True)
    project_id = fields.Many2one(
        'project.project', related='order_id.project_id', store=True)

    sub_project = fields.Many2one(
        'sub.project', 'Sub Project', related='order_id.sub_project', store=True)

    task_category = fields.Many2many(
        'task.category', 'cat_wizard_rels', 'cat_id', 'wizard_id')
    material_category = fields.Many2many(
        'product.category', 'prod_cat_wizard_line_rel', 'wizard_id', 'cat_id', related='order_id.material_category')
    me_sequence = fields.Char(readonly=True)
    requisition_name = fields.Many2one('purchase.requisition', 'Requisition')
    estimation_id = fields.Many2one('task.material.line', 'Estimate No.')

    @api.onchange('current_req_qty')
    def onchnge_Requisition_qty(self):
        if self.current_req_qty > (self.quantity - self.Requisition_as_on_date):
            raise UserError(_('Please enter valid Requisition Quantity.'))

    @api.onchange('current_order_qty')
    def onchnge_order_qty(self):
        if self.current_order_qty > (self.requisition_qty - self.total_ordered_qty):
            raise UserError(
                _('Order quantity must be less than requisition quantity'))

    @api.model
    def get_current_req_qty(self):
        for line in self:
            current_req_qty = line.quantity - line.Requisition_as_on_date
            line.update({'current_req_qty': (current_req_qty)})
        return current_req_qty

    def get_ordered_qty(self, id):
        domain = []
        task_category = []
        material_category = []
        domain.append(('project_wbs', '=', self.order_id.id))
        domain.append(('project_id', '=', self.project_id.id))
        if self.group_id:
            domain.append(('group_id', '=', self.group_id.id))
        if self.task_id:
            domain.append(('material_line_id', '=', self.task_id.id))
        if self.material:
            domain.append(('material_id', '=', self.material_id.id))

        if self.task_category:
            for i in self.task_category:
                task_category.append(i.id)
            domain.append(('task_category', 'in', task_category))

        if self.material_category:
            for i in self.material_category:
                material_category.append(i.id)
            domain.append(('material_category', 'in', material_category))
        requisition_obj = self.env['purchase.requisition'].search(domain)
        return str(1)
