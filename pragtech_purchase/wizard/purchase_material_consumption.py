from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class PurchaseconsumptionWizard(models.TransientModel):
    _name = 'purchase.consumption.wizard'
    _description = 'Purchase Consumption Wizard'

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
        'Note:', default='You can only add consumption for approved material for current vendor')
    name = fields.Many2one('project.task', 'Project WBS Name', domain=[
        ('is_wbs', '=', True), ('is_task', '=', False)], required=True)
    project_id = fields.Many2one('project.project', 'Project', required=True)
    sub_project = fields.Many2one('sub.project', 'Sub Project', required=True)
    task_category = fields.Many2many(
        'task.category', 'consumption_cat_wizard_rel', 'cat_id', 'wizard_id')
    material_category = fields.Many2many(
        'product.category', 'cons_wizard_prod_cat_rel', 'cat_id', 'wizard_id')
    material = fields.Many2one('product.product', 'Material')
    group_id = fields.Many2one('project.task', 'Task Group')
    task_id = fields.Many2one('project.task', 'Task')
    consumption_ids = fields.One2many(
        'purchase.consumption.wizard.line', 'order_id')
    to_date = fields.Date(
        'To Date', default=fields.date.today(), required=True)
    from_date = fields.Date(
        'From Date', default=(datetime.now() + timedelta(days=-30)).date(), required=True)
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
        return {'domain': {'task_id': [('parent_id', '=', self.group_id.id),
                                       ('is_task', '=', True),
                                       ('project_wbs_id', '=', self.name.id)]}}

    @api.depends('category_id')
    @api.onchange('category_id')
    def task_category_onchange(self):
        return {'domain': {'task_id': [
            ('category_id', '=', self.task_category.id),
            ('is_task', '=', True),
            ('project_wbs_id', '=', self.name.id)]}}

    def get_is_red(self, material_id, partner_id):
        product_id = self.env['product.product'].search(
            [('id', '=', material_id)])
        price_info = self.env['product.supplierinfo'].search(
            [('product_tmpl_id', '=', product_id.product_tmpl_id.id), ('is_active', '=', True),
             ('name', '=', partner_id)])
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
        for line in self.consumption_ids:
            line.is_use = self.is_use

    #             line.write({'is_use': self.is_use})

    def write(self, vals):
        if self._context.get('project_id'):
            vals.update({'project_id': self._context.get('project_id')})

        if self._context.get('project_wbs'):
            vals.update({'name': self._context.get('project_wbs')})

        if self._context.get('sub_project'):
            vals.update({'sub_project': self._context.get('sub_project')})

        res = super(PurchaseconsumptionWizard, self).write(vals)
        return res

    @api.model
    def default_get(self, fields_list):
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

    # Searching to create purchase consumption according user input

    @api.depends('project_id', 'sub_project', 'name', 'group_id',
                 'task_category', 'task_id', 'material_category',
                 'material')
    def compute_consumptions_lines(self):

        self.consumption_ids.unlink()
        # Search from different fields and add consumption depending on search
        # result
        project_task_obj = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id),
             ('name', '=', self.name.name),
             ('sub_project', '=', self.sub_project.id)])
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
            location_ids = self.env['stock.quant'].search(
                [('product_id.id', '=', line.material_id.id), ('location_id.usage', '=', 'internal')], limit=1)

            consumption_records = self.env['purchase.consumption'].search([('material_id', '=', line.material_id.id), (
                'project_id', '=', self.project_id.id), ('sub_project', '=', self.sub_project.id),
                                                                           ('project_wbs', '=', self.name.id),
                                                                           ('state', '=', 'confirm')])
            consumption_remain = 0.0
            for cosum_line in consumption_records:
                consumption_remain += cosum_line.current_consum_qty
            vals = {
                'material_id': line.material_id.id,
                'quantity': line.material_uom_qty,
                'rate': line.material_rate,
                'task_id': line.material_line_id.id,
                'group_id': line.group_id.id,
                'consumption_date': datetime.now(),
                'task_category': line.material_line_id.category_id,
                'unit': line.material_uom.id,
                'product_location_id': location_ids.location_id.id,
                'me_sequence': line.name,
                'consumption_as_on_date': consumption_remain,
                'current_consum_qty': line.material_uom_qty - consumption_remain,
                # 'consumption_id': self.id,
                'order_id': self.id,
                'estimation_id': line.id,

            }
            abcd = self.consumption_ids.create(vals)
            abcd.onchange_product_location_id()
        view_id = self.env.ref(
            'pragtech_purchase.purchase_consumption_wizard_view').id

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.consumption.wizard',
            'res_id': self.id,
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    """ Create Purchase consumptions"""

    def create_consumptions(self):
        vals = {}
        req_ids = []
        stage = self.env['stage.master'].search([('draft', '=', True)])
        for line in self.consumption_ids:
            total_qty = 0
            domain = []
            domain.append(('project_wbs', '=', line.project_wbs.id))
            domain.append(('project_id', '=', line.project_id.id))
            domain.append(('sub_project', '=', line.sub_project.id))
            if line.group_id:
                domain.append(('group_id', '=', line.group_id.id))
            if line.task_id:
                domain.append(('task_id', '=', line.task_id.id))
            if line.material_id:
                domain.append(('material_id', '=', line.material_id.id))
            consumption_obj = self.env['purchase.consumption'].search(domain)
            for consumption_obj in consumption_obj:
                total_qty = total_qty + consumption_obj.quantity
            if line.is_use:

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
                    'consumption_date': datetime.now(),
                    'stage_id': stage.id,
                    'product_location_id': line.product_location_id.id,
                    'estimated_qty': line.quantity,
                    'consumption_as_on_date': line.consumption_as_on_date,
                    'current_consum_qty': line.current_consum_qty,
                    'me_sequence': line.me_sequence,
                    'specification': line.specification,
                    'estimation_id': line.estimation_id.id,

                }
                res = self.env['purchase.consumption'].create(vals)

                # Rmoved code for Stock move line creation
                if line.current_consum_qty > (line.quantity - line.consumption_as_on_date):
                    raise UserError(
                        _('Please enter valid consumption Quantity.'))
                vals = {
                    'date': datetime.now(),
                    'remark': 'Created by ' + (self.env['res.users'].browse(self._context.get('uid'))).name,
                    'model': 'purchase.consumption',
                    'res_id': res.id,
                    'author_id': self._context.get('uid'),
                    'to_stage': stage.id
                }
                self.env['mail.messages'].create(vals)
                req_ids.append(res.id)

        view_id = self.env.ref(
            'pragtech_purchase.purchase_consumption_tree_view').id
        # context = self._context.copy()
        return {
            'name': 'Consumption',
            'view_type': 'form',
            'view_mode': 'tree', 'form'
                                 'views': [(view_id, 'tree')],
            'res_model': 'purchase.consumption',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'domain': [('id', 'in', req_ids)],
            'context': {'project_id': self.project_id.id, 'project_wbs': self.name.id,
                        'sub_project': self.sub_project.id},
        }

    """search consumptions on purchase order"""

    @api.depends('project_id', 'name', 'material_category', 'material', 'to_date', 'from_date')
    def search_consumptions_on_po(self):
        self.consumption_ids.unlink()
        # Search from different fields and add consumption depending on search
        # result
        if self.from_date > self.to_date:
            raise UserError("From Date should be <= To Date")
        Purchase_order_obj = self.env['purchase.order'].browse(
            self._context.get('active_id'))
        consumption_list = []
        domain = []
        material_category = []
        # Get Approved stage from stage.master table
        stage_master_obj = self.env['stage.master'].search(
            [('approved', '=', True)], limit=1)
        domain.append(('stage_id', '=', stage_master_obj.id))
        domain.append(('project_id', '=', self.project_id.id))
        domain.append(('project_wbs', '=', self.name.id))
        domain.append(('consumption_date', '>=', self.from_date))
        domain.append(('consumption_date', '<=', self.to_date))
        if self.material:
            domain.append(('material_id', '=', self.material.id))

        if self.material_category:
            for i in self.material_category:
                material_category.append(i.id)
            domain.append(('material_category', 'in', material_category))
        purchase_consumption_obj = self.env[
            'purchase.consumption'].search(domain)
        for line in purchase_consumption_obj:

            product_supplier_obj = self.env['product.supplierinfo'].search(
                [('product_name', '=', line.material_id.name), ('is_active', '=', True),
                 ('name', '=', Purchase_order_obj.partner_id.id)])
            if (line.current_consum_qty - line.total_ordered_qty) > 0:

                price_info = self.get_is_red(
                    line.material_id.id, Purchase_order_obj.partner_id.id)
                if product_supplier_obj:
                    vals = {
                        'project_id': self.project_id.id,
                        'project_wbs': self.name.id,
                        'consumption_name': line.id,
                        'material_id': line.material_id.id,
                        'quantity': line.quantity,
                        'unit': line.unit.id,
                        'task_id': line.task_id.id,
                        'group_id': line.group_id.id,
                        'consumption_name': line.id,
                        'consumption_qty': line.current_consum_qty,
                        'total_ordered_qty': line.total_ordered_qty,
                        'current_order_qty': line.current_consum_qty - line.total_ordered_qty,
                        'me_sequence': line.me_sequence,
                        'specification': line.specification
                    }
                else:
                    vals = {
                        'project_id': self.project_id.id,
                        'project_wbs': self.name.id,
                        'consumption_name': line.id,
                        'material_id': line.material_id.id,
                        'quantity': line.quantity,
                        'unit': line.unit.id,
                        'task_id': line.task_id.id,
                        'group_id': line.group_id.id,
                        'consumption_name': line.id,
                        'consumption_qty': line.current_consum_qty,
                        'total_ordered_qty': line.total_ordered_qty,
                        'current_order_qty': 0,
                        'me_sequence': line.me_sequence,
                        'specification': line.specification
                    }
                if price_info:
                    vals.update({'rate': price_info.price, 'is_red': False})
                else:
                    vals.update({'rate': line.rate, 'is_red': True})
                consumption_list.append((0, 0, vals))
        self.update({'consumption_ids': consumption_list})

        view_id = self.env.ref(
            'pragtech_purchase.consumption_wizard_for_po').id
        return {
            'name': 'Add consumption',
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.consumption.wizard',
            'res_id': self.id,
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    """ Add consumptions on PO consumption (Above Purchase Order Lines)"""

    def add_consumption(self):
        Purchase_order_obj = self.env['purchase.order'].browse(
            self._context.get('active_id'))
        po_consumption_line_obj = self.env['purchase.consumption'].search(
            [('order_id', '=', self._context.get('active_id'))])
        old_po_consumption_lines = [
            line.consumption_id for line in po_consumption_line_obj]
        vals = {}
        for line in self.consumption_ids:
            if line.is_use:
                if line.current_order_qty > (line.consumption_qty - line.total_ordered_qty):
                    raise UserError(
                        _('Order quantity must be less than consumption quantity.'))
                if line.current_order_qty == 0:
                    raise UserError(_('Please enter valid consumption Quantity'))
                if line.is_red and line.is_use:
                    raise UserError(
                        'You can only add consumption for approved material for current vendor')
                if line.consumption_name not in old_po_consumption_lines and line.current_order_qty > 0 and line.current_order_qty <= (
                        line.consumption_qty - line.total_ordered_qty):

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
                        'current_consum_qty': (line.current_consum_qty),
                        'consumption_qty': line.consumption_qty,
                        'total_ordered_qty': line.total_ordered_qty,
                        'current_order_qty': line.current_order_qty,
                        'me_sequence': line.me_sequence,
                        'order_id': self._context.get('active_id'),
                        'consumption_id': line.consumption_name.id,
                        'specification': line.specification,
                    }
                    # and Purchase_order_obj.order_id.state=='shipment'
                    if Purchase_order_obj.stage_id.approved:
                        stage_master_obj = self.env['stage.master'].search(
                            [('amend_and_draft', '=', True)], limit=1)
                        Purchase_order_obj.stage_id = stage_master_obj.id
                        Purchase_order_obj.flag = False
                        Purchase_order_obj.state = 'draft'
                    self.env['purchase.consumption'].create(vals)
        Purchase_order_obj.compute_po_lines(
            Purchase_order_obj, self.name, self.project_id)


class purchaseconsumptionWizardLine(models.TransientModel):
    _name = 'purchase.consumption.wizard.line'
    _description = 'Purchase Consumption Wizard Line'

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
    name = fields.Char('consumption No')
    group_id = fields.Many2one('project.task', 'Task Group')
    task_id = fields.Many2one('project.task', 'Task')
    flag = fields.Boolean('Flag', default=False)
    material_id = fields.Many2one('product.product', 'Material')
    consumption_date = fields.Date(
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
    consumption_qty = fields.Float('consumption Qty')
    current_order_qty = fields.Float('Current Order Qty')

    # latest as suggested on 26/12/16 quantity fields
    estimated_qty = fields.Float('Estimated Qty')
    consumption_as_on_date = fields.Float('consumption as on date')
    # , compute='get_current_consum_qty'
    current_consum_qty = fields.Float(
        'Current consumption Qty', readonly=False)

    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], 'Status')
    priority = fields.Selection([('high', 'High'), ('low', 'Low')], 'Priority')
    brand_id = fields.Many2one('brand.brand', 'Brand')
    consumption_type = fields.Selection(
        [('estimated', 'Estimated'), ('non_estimated', 'Non Estimated')], 'Type')
    order_id = fields.Many2one(
        'purchase.consumption.wizard', 'consumption_ids')
    unit = fields.Many2one('uom.uom', 'UOM', required=True)
    rate = fields.Float('Rate')
    procurement_type = fields.Selection([('New Purchase from Supplier', 'New Purchase from Supplier'),
                                         ('Cash Purchase ', 'Cash Purchase '),
                                         ('IST from other sites', 'IST from other sites'), ], "Procurement Type")
    warehouse_id = fields.Char('Procurement Type', readonly=True)
    product_location_id = fields.Many2one('stock.location', 'Location')
    #     purchase_ids = fields.Many2many('purchase.order', string='Purchase Order')
    #     consumption_fulfill = fields.Boolean('Req fulfill')
    stage_id = fields.Many2one(
        'transaction.stage', domain=[('model', '=', 'consumption.order.line')])
    project_wbs = fields.Many2one(
        'project.task', related='order_id.name', store=True)
    project_id = fields.Many2one(
        'project.project', related='order_id.project_id', store=True)

    sub_project = fields.Many2one(
        'sub.project', 'Sub Project', related='order_id.sub_project', store=True)

    # material_category = fields.Many2many(
    #     'product.category', 'cons_wizard_prod_cat_rels', 'cat_id', 'wizard_line_id',
    #     related='order_id.material_category', store=True)
    material_category = fields.Many2many(
        'product.category', 'cons_wizard_prod_cat_rels', 'cat_id', 'wizard_line_id')
    task_category = fields.Many2many(
        'task.category', 'consumption_cat_wizard_rels', 'cat_id', 'wizard_id')
    me_sequence = fields.Char(readonly=True)
    consumption_name = fields.Many2one('purchase.consumption', 'Consumption')
    estimation_id = fields.Many2one('task.material.line', 'Estimate No.')

    @api.onchange('current_consum_qty')
    def onchnge_consumption_qty(self):
        if self.current_consum_qty > (self.quantity - self.consumption_as_on_date):
            raise UserError(_('Please enter valid consumption Quantity.'))

    @api.onchange('is_use')
    def onchange_product_location_id(self):
        stock_quant_id = self.env['stock.quant']
        location_id_list = []
        if self.material_id:
            location_ids = stock_quant_id.search(
                [('product_id.id', '=', self.material_id.id)])
            for id in location_ids:
                location_id_list.append(id.location_id.id)
                if id.quantity and id.location_id.usage == 'internal':
                    self_quantity = self.quantity - self.consumption_as_on_date
                    if self_quantity <= (id.quantity - id.reserved_quantity):
                        self.current_consum_qty = self_quantity
                    else:
                        self.current_consum_qty = id.quantity - id.reserved_quantity
            return {'domain': {'product_location_id': [('id', 'in', location_id_list), ('usage', '=', 'internal')]}}
        return {'domain': {'product_location_id': [('id', 'in', [])]}}

    @api.onchange('current_order_qty')
    def onchnge_order_qty(self):
        if self.current_order_qty > (self.consumption_qty - self.total_ordered_qty):
            raise UserError(
                _('Order quantity must be less than consumption quantity'))

    @api.model
    def get_current_consum_qty(self):
        for line in self:
            current_consum_qty = line.quantity - line.consumption_as_on_date
            line.update({'current_consum_qty': (current_consum_qty)})
        return current_consum_qty

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
        consumption_obj = self.env['purchase.consumption'].search(domain)
        return str(1) 
