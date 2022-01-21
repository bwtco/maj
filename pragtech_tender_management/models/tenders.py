
from odoo import api, fields, models

from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import UserError,UserError
from odoo.osv import expression



class TendersTenders(models.Model):
    _name = 'tenders.tenders'
    _inherit = ["website.seo.metadata", 'website.published.multi.mixin']
    _rec_name = 'tender_name'
    _description = 'Tenders'

    name = fields.Char('Name')
    tender_name = fields.Char('Tender Name')
    comment = fields.Char(compute='_compute_comment')
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State')
    country_id = fields.Many2one('res.country', string='Country')
    user_id = fields.Many2one('res.partner', 'Responsible')
    start_date = fields.Datetime("Bid from", default=fields.Datetime.today)
    end_date = fields.Datetime("Bid to")  # no start and end = always active
    top_rank = fields.Char('Top rank')
    tender_line_id = fields.One2many('tenders.tenders.line', 'line_id')
    tender_overhead_id = fields.One2many('tenders.overhead', 'overhead_id')
    tender_labour_id = fields.One2many('tenders.labour', 'labour_id')
    tender_question_ids = fields.One2many('question.question', 'question_id', 'Tender Questions')
    department = fields.Many2one('res.department', string='Department', help='Name of the department inviting tender')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approve', 'Approve'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('rejected', 'Rejected'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft')
    website_published = fields.Boolean(default=True)
    bids_id = fields.Many2one('bids.bids')
    count_bids = fields.Integer(compute='_compute_bids_id')
    all_total = fields.Float(default=0.0)
    total_budget = fields.Float(string='Total Budget')
    earnest_money_deposit = fields.Float(string='Earnest Money Deposit')
    performance_security_deposit = fields.Float(string='Performance Security Deposit')
    liquidated_damage = fields.Float(string='Liquidated Damage')
    unliquidated_damage = fields.Float(string='Unliquidated Damage')
    pre_bid_meeting_date = fields.Datetime("Pre-bid Meeting Date")
    pre_bid_meeting_mom = fields.Html('Pre-bid Meeting MOM')

    def action_view_bids(self):
        tree_view_id = self.env.ref('pragtech_tender_management.bids_tree_view').id
        form_view_id = self.env.ref('pragtech_tender_management.bids_form_view').id
        bids = []
        if self.tender_name:
            bids.append(self.tender_name)
            return {
                'name': self.name,
                'res_model': 'bids.bids',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree',
                'view_type': 'form',
                'view_id': tree_view_id,
                'domain': [('tender_id', '=', bids)],
                'views': [
                    (tree_view_id, 'tree'),
                    (form_view_id, 'form'),
                ],
                'res_id': False,
                'context': False,
            }

    @api.depends('bids_id')
    def _compute_bids_id(self):
        for bids in self:
            bids_ids = bids.env['bids.bids'].search([('tender_id', 'in', bids.tender_name)])
            bids.count_bids = len(bids_ids)

    def action_tender_submit(self):
        self.write({
            'state': 'submitted'
        })

    def action_tender_approve(self):
        self.write({
            'state': 'approve'
        })

    def action_tender_cancel(self):
        self.write({
            'state': 'rejected'
        })

    def _compute_website_url(self):
        super(TendersTenders, self)._compute_website_url()
        for tenders in self:
            tenders.website_url = "/tenders/view/%s" % slug(tenders)


class TendersTendersLine(models.Model):
    _name = 'tenders.tenders.line'
    _description = 'Tenders Line'

    line_id = fields.Many2one('tenders.tenders')
    product_id = fields.Many2one('product.product')
    line_description = fields.Text(string='Description')
    product_uom_qty = fields.Float('Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Product UoM')
    material_last_price = fields.Float('Last price')
    material_your_price = fields.Float()

    @api.model
    def create(self, vals):
        if vals.get('product_uom_qty') < 1.0:
            raise UserError('Material quantity should be greater than or equal to 1')
        if not vals.get('product_uom'):
            raise UserError('Please select material units')
        return super(TendersTendersLine, self).create(vals)

    def write(self, vals):
        result = super(TendersTendersLine, self).write(vals)
        for rec in self:
            if rec.product_uom_qty < 1.0:
                raise UserError('Material quantity should be greater than or equal to 1')
            if not rec.product_uom:
                raise UserError('Please select material units')
        return result

    @api.onchange('product_id')
    def product_id_change(self):
        vals = {}
        if self.product_id:
            vals = {'line_description': self.product_id.name}
        return {'value': vals}


class TendersLabour(models.Model):
    _name = 'tenders.labour'
    _description = 'Tenders Labour'

    labour_id = fields.Many2one('tenders.tenders')
    tender_labour_labour_id = fields.Many2one('labours.labour', 'Name')
    labour_description = fields.Text(string='Description')
    labour_qty = fields.Float('Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Labour UoM')
    labour_last_price = fields.Float('Last price')
    labour_your_price = fields.Float()

    @api.model
    def create(self, vals):
        if vals.get('labour_qty') < 1.0:
            raise UserError('Labour quantity should be greater than or equal to 1')
        if not vals.get('product_uom'):
            raise UserError('Please select labour units')
        return super(TendersLabour, self).create(vals)

    def write(self, vals):
        result = super(TendersLabour, self).write(vals)
        for rec in self:
            if rec.labour_qty < 1.0:
                raise UserError('Labour quantity should be greater than or equal to 1')
            if not rec.product_uom:
                raise UserError('Please select labour units')
        return result

    @api.onchange('tender_labour_labour_id')
    def labour_details(self):
        vals_labour = {}
        if self.tender_labour_labour_id:
            vals_labour = {
                'labour_description': self.tender_labour_labour_id.labour_description
                    }
        return {'value': vals_labour}


class LaboursLabours(models.Model):
    _name = 'labours.labour'
    _description = 'Labours Labours'

    name = fields.Char()
    labour_description = fields.Text(string='Description')
    labour_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('uom.uom', string='Labour UoM')
    labour_last_price = fields.Float('Last price')


class OverheadOverhead(models.Model):
    _name = 'overhead.overhead'
    _description = 'Overhead Overhead'

    name = fields.Char()
    overhead_description = fields.Text(string='Description')
    overhead_qty = fields.Float('Quantity')
    product_uom = fields.Many2one('uom.uom', string='Overhead UoM')
    overhead_last_price = fields.Float('Last price')


class TendersOverheads(models.Model):
    _name = 'tenders.overhead'
    _description = 'Tenders Overhead'

    overhead_id = fields.Many2one('tenders.tenders')
    tender_overhead_overhead_id = fields.Many2one('overhead.overhead', 'Name')
    overhead_description = fields.Text(string='Description')
    overhead_qty = fields.Float('Quantity', default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Overhead UoM')
    overhead_last_price = fields.Float('Last price')
    overhead_your_price = fields.Float()

    @api.model
    def create(self, vals):
        if vals.get('overhead_qty') < 1.0:
            raise UserError('Overhead quantity should be greater than or equal to 1')
        if not vals.get('product_uom'):
            raise UserError('Please select overhead units')
        return super(TendersOverheads, self).create(vals)

    def write(self, vals):
        result = super(TendersOverheads, self).write(vals)
        for rec in self:
            if rec.overhead_qty < 1.0:
                raise UserError('Overhead quantity should be greater than or equal to 1')
            if not rec.product_uom:
                raise UserError('Please select overhead units')
        return result

    @api.onchange('tender_overhead_overhead_id')
    def overhead_details(self):
        vals_overhead = {}
        if self.tender_overhead_overhead_id:
            vals_overhead = {
                'overhead_description': self.tender_overhead_overhead_id.overhead_description
            }
        return {'value': vals_overhead}


class ResDepartment(models.Model):
    _name = "res.department"
    _description = "Department master"
    name = fields.Char(string="Name", required=True, help="Name of the department")


class TenderQuestions(models.Model):
    _name = "tender.questions"
    _description = "Tender Questions"

    name = fields.Char(string='Text', required=True)
    type = fields.Selection([('text', 'Text'), ('number', 'Numerical')])


class Question(models.Model):
    _name = 'question.question'
    _description = 'Rating Questionnaire'
    question_id = fields.Many2one('tenders.tenders')
    tender_question_id = fields.Many2one('tender.questions', 'Name')
    type = fields.Selection([('text', 'Text'), ('number', 'Numerical')])

    @api.onchange('tender_question_id')
    def questionnaire_details(self):
        vals_question = {}
        if self.tender_question_id:
            vals_question = {
                'type': self.tender_question_id.type
            }
        return {'value': vals_question}
