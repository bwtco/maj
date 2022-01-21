from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta


class PaymentSchedule(models.Model):
    _name = 'payment.schedule'
    _description = 'Payment Schedule'
    _rec_name = 'task_name'

    task_name = fields.Char(related='task_id.name')
    amount_to_release = fields.Float(
        'Amount to Release (%)', help=' Percentage amount to release after completion of respective task in .')
    task_id = fields.Many2one('project.task', 'Task')
    workorder_line_id = fields.Many2one('work.order.line', 'Work order Line')
    project_wbs = fields.Many2one('project.task')
    completion_percent = fields.Float('Completion Percent Till Date')
    completion_id = fields.Many2one('work.completion', 'Work Completion')
    task_ids_list = []

    def get_task_ids(self, wbs):
        self.project_wbs = wbs

    @api.model
    def default_get(self, fields_list):
        return models.Model.default_get(self, fields_list)
