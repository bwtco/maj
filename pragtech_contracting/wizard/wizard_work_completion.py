from datetime import datetime, timedelta
import time
from odoo.tools.float_utils import float_is_zero, float_compare
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
import threading
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, UserError, RedirectWarning


class WizardWorkCompletion(models.TransientModel):
    _name = "wizard.work.completion"
    _description = "Wizard Completion"

    workorder_id = fields.Many2one('work.order', 'WorkOrder')
    project_wbs = fields.Many2one('project.task', 'Project WBS', domain=[
                                  ('is_wbs', '=', True), ('is_task', '=', False)], required=True)
    project_id = fields.Many2one('project.project', 'Project', required=True)
    sub_project = fields.Many2one('sub.project', 'Sub Project', required=True)
    task_category = fields.Many2many('task.category', 'task_req_task_categ_rel', 'requisition_id', 'task_category_id',
                                     string='Task Category')
    # , 'labour_req_labour_categ_rel', 'requisition_id', 'labour_category_id',
    labour_category = fields.Many2many(
        'labour.category', 'wo_completion_lbr_cat_rel', 'labour_cat_id', 'wo_compl_wizard_id', string='Labour Category')

    labour_id = fields.Many2one('labour.master', 'Labour')
    group_id = fields.Many2one('project.task', 'Group')
    task_id = fields.Many2one('project.task', 'Task')
    completion_task_line_ids = fields.One2many('wizard.work.completion.task', 'work_completion_id', string='Requisition Order')
    from_date = fields.Date('From Date', default=str(datetime.now() + timedelta(days=-30)).split(' ')[0], required=True)
    to_date = fields.Date('To Date', default=str(fields.datetime.now() + timedelta(days=1)).split(' ')[0], required=True)
    is_use = fields.Boolean(' ')

    task_date_type = fields.Selection([('planned', 'Planned'), ('actual', 'Actual')],
                                      string='Task Date Type', default='planned')  # #,'Search Task having'
    date_type = fields.Selection([('start_date', 'Start Date'), ('finish_date', 'Finish Date')], default='start_date', string='Date Type')

    completion = fields.Selection([('all', 'All'), ('completed', 'Completed'), ('not_completed', 'Not Completed')], default='all')
#     """This method applies domain on all dropdown,as wbs of selected project and group of selected wbs and so on"""
#     @api.depends('project_id', 'project_wbs', 'group_id', 'task_category')
#     @api.onchange('project_id', 'project_wbs', 'group_id', 'task_category')
#     def project_onchange(self):
#         project_lst = []
#         task_lst = []
#         group_lst = []
#         self.name_lst = []
#         if self.project_id:
#             project_ids = self.env['project.task'].search([('project_id', '=', self.project_id.id)])
#             for i in project_ids:
#                 for line in i.labour_estimate_line:
#                     if line:
#                         task_lst.append(line.labour_line_id.id)
#                         group_lst.append(line.labour_line_id.category_id.id)
#                 project_lst.append(i.name)
#         if self.project_wbs:
#             project_ids = self.env['task.labour.line'].search([('wbs_id', '=', self.project_wbs.id)])
#             for i in project_ids:
#                 self.name_lst.append(i.group_id.id)
#         self.group_domain1=str(self.name_lst)
#
#         return {'domain': {'project_wbs': [('name', 'in', project_lst)],'group_id': [('id', 'in', group_lst)] ,'task_category': [('id', 'in', group_lst)],
#                            'task_id': [('id', '=', task_lst), ('is_task', '=', True)]}}
#
#         project_wbs_lst = []
#         labour_list = []
#         task_list = []
#         group_list = []
#         labour_category = []
#         task_category = []
#         project_ids = self.env['project.task'].search([('project_id', '=', self.project_id.id)])
#         for i in project_ids:
#             project_wbs_lst.append(i.name)
#         if self.project_wbs:
#             project_task_obj = self.env['project.task'].search([('project_id', '=', self.project_id.id), ('name', '=', self.project_wbs.name)])
#             for line in project_task_obj.labour_estimate_line:
#                 labour_list.append(line.labour_id.id)
#                 task_list.append(line.labour_line_id.id)
#                 group_list.append(line.group_id.id)
#                 labour_category.append(line.labour_id.category_id.id)
#                 task_category.append(line.labour_line_id.category_id.id)
# return {'domain': { 'task_id': [('id', 'in', task_list)], 'group_id':
# [('id', 'in', group_list)], 'labour_category': [('id', 'in',
# labour_category)], 'task_category': [('id', 'in', task_category)],
# 'labour_id': [('id', 'in', labour_list)]}}

    @api.depends('sub_project')
    @api.onchange('sub_project')
    def sub_project_onchange(self):
        project_lst = []
        project_ids = self.env['project.task'].search(
            [('project_id', '=', self.project_id.id), ('sub_project', '=', self.sub_project.id)])
        for i in project_ids:
            project_lst.append(i.name)
        return {'project_wbs': {'name': [('name', 'in', project_lst)]}}

    @api.depends('task_category')
    @api.onchange('task_category')
    def task_category_onchange(self):
        cat_list = []
        for line in self.task_category:
            cat_list.append(line.id)
        return {'domain': {'task_id': [('category_id', 'in', cat_list), ('is_task', '=', True), ('project_wbs_id', '=', self.project_wbs.id)]}}

    @api.depends('labour_category')
    @api.onchange('labour_category')
    def labour_category_onchange(self):
        cat_list = []
        for line in self.labour_category:
            cat_list.append(line.id)
        return {'domain': {'labour_id': [('category_id', '=', self.labour_category.id), ('is_labour', '=', True)]}}

    @api.depends('project_id', 'project_wbs', 'group_id', 'task_category', 'task_id', 'labour_category', 'labour_id')
    def compute_task_lines(self):
        # Search from different fields and add requisition depending on search
        # result
        self.completion_task_line_ids.unlink()
        vals = {}
        workorder_list = []
        domain = []
        wo_domain = []
        task_category_lst = []
        labour_category_lst = []
        if self.project_id:
            wo_domain.append(('project_id', '=', self.project_id.id))
        if self.project_wbs:
            wo_domain.append(('project_wbs', '=', self.project_wbs.id))
        if self.sub_project:
            wo_domain.append(('sub_project', '=', self.sub_project.id))
        if self.workorder_id:
            wo_domain.append(('id', '=', self.workorder_id.id))
        workorder_obj = self.env['work.order'].search(wo_domain)
        for order in workorder_obj:
            for line in order:
                workorder_list.append(line.id)
        domain.append(('order_id', 'in', workorder_list))
        if self.task_category:
            for i in self.task_category:
                task_category_lst.append(i.id)
            domain.append(('task_category', 'in', task_category_lst))
        if self.labour_category:
            for i in self.labour_category:
                labour_category_lst.append(i.id)
            domain.append(('category_id', 'in', labour_category_lst))
        if self.labour_id:
            domain.append(('labour_id', '=', self.labour_id.id))
        if self.task_id:
            domain.append(('task_id', '=', self.task_id.id))

        wo_line_obj = self.env['work.order.line'].search(domain)

        for wo_line in wo_line_obj:
            for line in wo_line.payment_schedule_line_ids:

                vals.update({'work_completion_id': self.id,
                             'labour_id': wo_line.labour_id.id,
                             'labour_uom_qty': wo_line.quantity,
                             'labour_uom': 6,
                             'labour_rate': wo_line.rate,
                             'workorder_id': wo_line.order_id.id,
                             'workorder_line_id': wo_line.id,
                             'amt_to_release': line.amount_to_release,
                             'payment_schedule_id': line.id
                             })

                if self.task_id:
                    if line.task_id == self.task_id:
                        vals.update({'task_id': self.task_id.id, })
                else:
                    vals.update({'task_id': line.task_id.id, })

                if self.completion == 'completed':
                    if line.completion_id.total_percent == 100.0:
                        self.env['wizard.work.completion.task'].create(vals)
                elif self.completion == 'not_completed':
                    if line.completion_id.total_percent < 100.0 and line.completion_id.total_percent > 0.0:
                        self.env['wizard.work.completion.task'].create(vals)
                else:
                    self.env['wizard.work.completion.task'].create(vals)

        view_id = self.env.ref('pragtech_contracting.work_requisition_wizard_form_view').id
        return {
            'name': _("Create Work Completion"),
            'context': self.env.context,
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.work.completion',
            'res_id': self.id,
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


class WizardWorkCompletionTask(models.TransientModel):
    _name = "wizard.work.completion.task"
    _description = "Wizard Work Completion Task"

    task_id = fields.Many2one('project.task', 'Task')
    remark = fields.Char('Remark')
    work_completion_id = fields.Many2one(
        'wizard.work.completion', 'Work Requisition')
    is_use = fields.Boolean(' ')
    project_id = fields.Many2one(
        'project.project', related='work_completion_id.project_id', store=True, string='Project')
    sub_project = fields.Many2one(
        'sub.project', related='work_completion_id.sub_project', string='Sub Project', required=True)
    project_wbs = fields.Many2one(
        'project.task', related='work_completion_id.project_wbs', store=True, string='Project Wbs')
    workorder_id = fields.Many2one('work.order', 'Workorder')
    workorder_line_id = fields.Many2one('work.order.line', 'WO Detail No')
    labour_estimate_sequence = fields.Char(readonly=True)
    labour_id = fields.Many2one('labour.master', string='Labour')
    labour_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    labour_uom_qty = fields.Float(string='Quantity', default=1.0)
    labour_rate = fields.Float(string='Rate', default=1.0)
    amt_to_release = fields.Float(string='Amount to release',
                                  help='This is amount to release after completion of task which is specified in payment schedule.')
    group_id = fields.Many2one('project.task', related='task_id.parent_task_id', store=True, string='Group')
    payment_schedule_id = fields.Many2one('payment.schedule', 'Payment Schedule')
#     labour_category = fields.Many2one('labour.category', related='labour_id.category_id', store=True, string='Labour Category')
#     task_category = fields.Many2one('task.category', related='task_id.category_id', store=True, string='Task Category')
#     date_start = fields.Datetime(string='Start Date', related='task_id.date_start', store=True)
#
#     planned_start_date = fields.Date(string='Planned Start Date', related='task_id.planed_start_date', store=True)
#     planned_finish_date = fields.Date(string='Planned Finish Date', related='task_id.planned_finish_date', store=True)
#     actual_start_date = fields.Date(string='Actual Finish Date', related='task_id.actual_start_date', store=True)
#     actual_finish_date = fields.Date(string='Actual Finish Date', related='task_id.actual_finish_date', store=True)

    def get_estimated_qty(self, task_id):
        task_estimation = self.env['task.labour.line'].search(
            [('labour_line_id', '=', task_id)], limit=1)
        return task_estimation.labour_uom_qty

    def complete_task(self):
        work_coml_obj = self.env['work.completion']
        res = self.env['work.completion']
        work_coml_obj = self.env['work.completion'].search([('project_id', '=', self.project_id.id), ('sub_project', '=', self.sub_project.id), (
            'project_wbs', '=', self.project_wbs.id), ('task_id', '=', self.task_id.id), ('labour_id', '=', self.labour_id.id), ('workorder_line_id', '=', self.workorder_line_id.id), ('workorder_id', '=', self.workorder_id.id)])
#         work_coml_obj = self.env['work.completion'].search([('task_id','=',self.task_id.id)])
        if not work_coml_obj:
            qty = self.get_estimated_qty(self.task_id.id)
#             if qty == 0:
#                 raise UserError(_('Estimation is zero'))
            vals = {

                'name': self.env['ir.sequence'].next_by_code('work.completion') or '/',
                'project_id': self.work_completion_id.project_id.id,
                'project_wbs': self.work_completion_id.project_wbs.id,
                'sub_project': self.work_completion_id.sub_project.id,
                'group_id': self.group_id.id,
                'labour_id': self.labour_id.id,
                'task_id': self.task_id.id,
                'forecast_completion': self.task_id.planned_finish_date,
                'estimated_qty': self.labour_uom_qty,
                'labour_estimate_sequence': self.labour_estimate_sequence,
                'workorder_id': self.workorder_id.id,
                'workorder_line_id': self.workorder_line_id.id,
                'contractor_id': self.workorder_id.partner_id.id,
                'amt_to_release': self.amt_to_release,
                'payment_schedule_id': self.payment_schedule_id.id

            }

            res = self.env['work.completion'].create(vals)
            msg_ids = {
                'date': datetime.now(),
                'author_id': self._context.get('uid'),
                'model': 'work.completion', 'res_id': res.id
            }
            self.env['mail.messages'].create(msg_ids)
        if res:
            """Setting Completion id in payment schedule table"""
            self.payment_schedule_id.completion_id = res.id
            view_id = self.env.ref(
                'pragtech_contracting.work_completion_form').id
            return {
                'name': _("Task Completion Progress"),
                'context': self.env.context,
                # 'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'res_model': 'work.completion',
                'res_id': res.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
            }
        if work_coml_obj and not res:
            view_id = self.env.ref(
                'pragtech_contracting.work_completion_form').id
            return {
                'name': _("Task Completion Progress"),
                'context': self.env.context,
                # 'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'res_model': 'work.completion',
                'res_id': work_coml_obj.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
            }
