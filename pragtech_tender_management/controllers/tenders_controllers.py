from odoo import http, fields
from odoo.addons.http_routing.models.ir_http import unslug
from odoo.http import request


class TendersController(http.Controller):
    @http.route(['/tender/<name>', '/tender'], type='http', auth="public", website=True)
    def tenders_bids(self, name, **post):
        # print("controller unslug",unslug(name))
        _, tenders_id = unslug(name)
        values = {}
        # print('\n\n\n NAME ::: ', post, name, tenders_id)

        bid_for_current_user = request.env['bids.bids'].sudo().search([('tender_id', '=', tenders_id)])
        tenderId = request.env['tenders.tenders'].sudo().search([('id', '=', tenders_id)])
        # print("bid_for_current_user", bid_for_current_user)
        if bid_for_current_user:
            # print("if bid_for_current_user", bid_for_current_user, tenderId)
            values_user = {}
            # print("\n\npre_bid meeting date",bid_for_current_user.bids_start_date,"\n",
            values_user.update({
                'bid_for_current_user': bid_for_current_user,
                'tenderId': tenderId
            })
            # print("\n\n\nvalues_user",values_user)
            return http.request.render('pragtech_tender_management.show_bids_info', values_user)
        else:
            # print("else bid_for_current_user", bid_for_current_user)
            if tenders_id or name:
                if tenders_id:
                    partner_sudo = request.env['tenders.tenders'].sudo().browse(tenders_id)
                    # print("\npartner_sudo in if", partner_sudo)
                else:
                    partner_sudo = request.env['tenders.tenders'].sudo().search([('name', '=', name)])
                    # print("\npartner_sudo in else", partner_sudo)
                is_website_publisher = request.env['res.users'].has_group('website.group_website_publisher')
                if partner_sudo.exists() and (partner_sudo.website_published or is_website_publisher):
                    # print("\n\n\n\n\npartner sudo material valuesssssssssss", partner_sudo.all_total)
                    values.update({
                        'main_object': partner_sudo,
                        'tendersproducts': partner_sudo,
                        'tendersproducts_published': partner_sudo.website_published,
                        'tender_line_id': partner_sudo.tender_line_id,
                        'tender_labour_id': partner_sudo.tender_labour_id,
                        'tender_overhead_id': partner_sudo.tender_overhead_id,
                        'tender_question_ids': partner_sudo.tender_question_ids

                    })
                    # print("values===========", values)
                return http.request.render('pragtech_tender_management.show_tenders_info', values)

    @http.route(['/tenders/view/<name>', '/tender/view/'], type='http', auth="public", website=True)
    def tender_website(self, name, **kwargs):
        _, tenders_id = unslug(name)
        values = {}
        if tenders_id or name:
            if tenders_id:
                partner_sudo = request.env['tenders.tenders'].sudo().browse(tenders_id)
            else:
                partner_sudo = request.env['tenders.tenders'].sudo().search([('name', '=', name)])
            is_website_publisher = request.env['res.users'].has_group('website.group_website_publisher')
            if partner_sudo.exists() and (partner_sudo.website_published or is_website_publisher):
                values.update({
                    'main_object': partner_sudo,
                    'tendersproducts': partner_sudo,
                    'tendersproducts_published': partner_sudo.website_published,
                })
            return http.request.render('pragtech_tender_management.list_tenders', values)

    @http.route('/tenders', type='http', auth='public', website=True)
    def all_tenders_website(self, **kwargs):
        publish_done = publish_all  = publish12 = request.env['tenders.tenders']
        # if request.env.user and request.env.user.partner_id and request.env.ref('base.group_public'):
        if request.env.user and request.env.user.partner_id:
            part_name = request.env.user.partner_id.name
            # publish_done = request.env['tenders.tenders'].sudo().search([('state','in',['done']),('top_rank','=',part_name)])
            publish_done = request.env['tenders.tenders'].sudo().search([('state','in',['done'])])

        publish_all = request.env['tenders.tenders'].sudo().search(['&', ('website_published', '=', True),
                                                                  ('state', 'in', ['approve', 'in_progress'])])
        for tender in publish_done:
            publish12 += tender
        for tend in publish_all:
            publish12 += tend
        # print("\n\n\nIn all tenders")
        value = {}
        user = request.env['res.users'].sudo()
        # print("publish12222222=======", part_name,publish12,publish_done,publish_all)
        if not user:
            value.update({'tendersproducts': publish12})
            # print("\n\n\npublish12=========", publish12)
        return request.render("pragtech_tender_management.list_all_tenders", value)

    @http.route('/tenders/update', type='http', methods=['POST'], auth="public", website=True, csrf=False)
    def bids_details_rank(self, **kw):
        # print("\n\n\n kw", kw)
        rank_value = {}
        # print("\n\n in ctroller ",kw['material_name_duplicate'].strip())

        tenderId = request.env['tenders.tenders'].search([('id', '=', int(kw.get('tender_id')))])
        if request.env.user._is_public():
            # print("You are not logged in")
            # print("Name of login", request.env.user.name)
            return request.render("pragtech_tender_management.logged_in_template")
        else:
            print("You are logged in")
            tenderId = None
            if kw.get('tender_id'):
                tenderId = request.env['tenders.tenders'].search([('id', '=', int(kw.get('tender_id')))])
                # print("\n\nIn controller kw",kw,"\ntenderId",tenderId)
            bids_obj = request.env['bids.bids']
            # print("\n\nbids_obj",bids_obj)
            # print("\nbids_name", tenderId.name, tenderId.street)
            # print("\n\nuser.id", request.env.user.id)
            bids_id = bids_obj.sudo().create({
                'name_of_bidder': request.env.user.id,
                'bids_name': tenderId.name,
                'bids_street': tenderId.street,
                'bids_street2': tenderId.street2,
                'bids_city': tenderId.city,
                'bids_zip': tenderId.zip,
                'bids_start_date': tenderId.start_date,
                'bids_end_date': tenderId.end_date,
                'bids_all_total': kw.get('total_amount_duplicate')
            })
            # print("bids_obj", bids_obj)
            # print("\n\n\nkw-------------", kw)
            tender_line_list = kw.get('tender_line_list')
            # print("\n\ntender_line_list", tender_line_list)
            t_list = []

            if tender_line_list:
                for tl in tender_line_list[1:-1].split(', '):
                    t_list.append(tl)
                # print("\nt_list line for", t_list, type(t_list))
                for tender_line in t_list:
                    # print("\ntender line for",tender_line)
                    tender_line_obj = request.env['tenders.tenders.line'].search([('id', '=', tender_line)])
                    bids_line_obj = request.env['bids.bids.line']
                    # print("\nmat your price",kw.get('material_your_price-' + str(tender_line)),
                    # "\n----------",kw.get('material_your_price'))
                    mat_vals = {}
                    mat_vals.update({
                        'bids_product_id': tender_line_obj.product_id.id,
                        'bids_description': tender_line_obj.line_description,
                        'bids_product_uom_qty': tender_line_obj.product_uom_qty,
                        'mat_last_price': tender_line_obj.material_last_price,
                        'mat_note': kw.get('material_note-' + str(tender_line)),
                        'mat_amount': kw.get('material_amount_duplicate-' + str(tender_line)),
                        'mat_your_price': kw.get('material_your_price-' + str(tender_line)),
                        'bids_product_uom': tender_line_obj.product_uom.id,
                        'line_id': bids_id.id
                        })
                    # print("\nmat_vals",mat_vals)
                    bids_line_obj.create(mat_vals)
            tender_labour_list = kw.get('tender_labour_list')
            # print("\ntender_line_list", tender_labour_list)
            tl_list = []
            tender_overhead_list = []
            if tender_labour_list:
                for tlabour in tender_labour_list[1:-1].split(', '):
                    tl_list.append(tlabour)
                # print("\nt_list line for", tl_list, type(tl_list))
                for tender_labour in tl_list:
                    # print("\ntender labour for", tender_labour)
                    tender_labour_obj = request.env['tenders.labour'].search([('id', '=', tender_labour)])
                    # print("tender_labour_obj",tender_labour_obj)
                    bids_line_obj = request.env['bids.labour']
                    # print("kw labour============",kw)
                    # print('labour_note-' + str(tender_labour_obj.id))
                    labour_vals = {}
                    # print("\nlabour qty", tender_labour_obj.labour_qty)
                    # print("\ntender_labour_labour_name",tender_labour_obj.tender_labour_labour_id.id)
                    labour_vals.update({
                        'labour_id': tender_labour_obj.tender_labour_labour_id.id,
                        'bids_labour_description': tender_labour_obj.labour_description,
                        'bids_labour_qty': tender_labour_obj.labour_qty,
                        'bids_labour_last_price': tender_labour_obj.labour_last_price,
                        'bids_labour_note': kw.get('labour_note-' + str(tender_labour_obj.id)),
                        'bids_labour_amount': kw.get('labour_amount_duplicate-' + str(tender_labour_obj.id)),
                        'bids_labour_product_uom': tender_labour_obj.product_uom.id,
                        'bids_labour_your_price': kw.get('labour_your_price-' + str(tender_labour_obj.id)),
                        'bids_labour_id': bids_id.id
                    })
                    # print("\nlabour_vals", labour_vals)
                    bids_line_obj.create(labour_vals)
                    tender_overhead_list = kw.get('tender_overhead_list')
            # print("\ntender_overhead_list", tender_overhead_list)
            to_list = []
            if tender_overhead_list:
                for toverhead in tender_overhead_list[1:-1].split(', '):
                    to_list.append(toverhead)
                # print("\nt_list line for", to_list, type(to_list))
                for tender_overhead in to_list:
                    # print("\ntender overhead for", tender_overhead)
                    tender_overhead_obj = request.env['tenders.overhead'].search([('id', '=', tender_overhead)])
                    # print("tender_overhead_obj", tender_overhead_obj)
                    bids_overhead_obj = request.env['bids.overhead']
                    # print("kw labour============",kw)
                    # print('labour_note-' + str(tender_labour_obj.id))
                    overhead_vals = {}
                    # print("\nlabour qty", tender_labour_obj.labour_qty)
                    # print("\ntender_labour_labour_name",tender_labour_obj.tender_labour_labour_id.id)
                    overhead_vals.update({
                        'overhead_id': tender_overhead_obj.tender_overhead_overhead_id.id,
                        'bids_overhead_description': tender_overhead_obj.overhead_description,
                        'bids_overhead_qty': tender_overhead_obj.overhead_qty,
                        'bids_overhead_last_price': tender_overhead_obj.overhead_last_price,
                        'bids_overhead_note': kw.get('overhead_note-' + str(tender_overhead_obj.id)),
                        'bids_overhead_amount': kw.get('overhead_amount_duplicate-' + str(tender_overhead_obj.id)),
                        'bids_overhead_product_uom': tender_overhead_obj.product_uom.id,
                        'bids_overhead_your_price': kw.get('overhead_your_price-' + str(tender_overhead_obj.id)),
                        'bids_overhead_id': bids_id.id
                    })
                    # print("\nlabour_vals", labour_vals)
                    bids_overhead_obj.create(overhead_vals)

            questionnaire_list = kw.get('questionnaire_list')
            # print("questionnaire_list", questionnaire_list)
            question_list = []
            if questionnaire_list:
                for tquestions in questionnaire_list[1:-1].split(', '):
                    question_list.append(tquestions)
                # print("\nt_list line for", question_list, type(question_list))

                for tender_question in question_list:
                    # print("\ntender questionnaire", tender_question)
                    tender_question_obj = request.env['question.question'].search([('id', '=', tender_question)])
                    # print("tender_question_obj", tender_question_obj)
                    bids_question_obj = request.env['bids.questions']
                    # print("kw labour============",kw)
                    # print('labour_note-' + str(tender_labour_obj.id))
                    question_vals = {}
                    # print("\nlabour qty", tender_labour_obj.labour_qty)
                    # print("\ntender_labour_labour_name",tender_labour_obj.tender_labour_labour_id.id)
                    question_vals.update({
                        # 'bids_question_ids': tender_question_obj.question_id.id,
                        'bids_id': bids_id.id,
                        'answer': kw.get('answer-' + str(tender_question_obj.tender_question_id.id)),
                        'question': tender_question_obj.tender_question_id.name,
                    })
                    # print("\nquestion_vals", question_vals)
                    bids_question_obj.create(question_vals)

            if bids_id:
                bids_id.bids_state_id = tenderId.state_id
                bids_id.bids_country_id = tenderId.country_id
                bids_id.bids_user_id = tenderId.user_id
                bids_id.tender_id = tenderId.id,
                # print("\n\nlab_your_price:::::::::::", lab_your_price)
                # print("\nbefore rank")
                rank_bid_id = request.env['bids.bids'].search([('tender_id', '=', bids_id.tender_id.id)])
                # print("rank_bid_id", rank_bid_id)
                rank = 0
                tmp_dict = {}
                sorted_dict = []
                for bid_id in rank_bid_id:
                    tmp_dict.update({bid_id.id: bid_id.bids_all_total})
                    # print("\n\n\ntmp_dict", tmp_dict)
                sorted_dict = sorted(tmp_dict.items(), key=lambda kv: (kv[1], kv[0]))
                # print("\n\n\n\nsorted_dict", sorted_dict)
                for ele in sorted_dict:
                    rank += 1
                    # print("\n\n ELEE ::: ", ele, type(ele[0]), bids_id.id)
                    if ele[0] == bids_id.id:
                        # print("\n\n\n\n YES", rank)
                        break
                # print("\n\n\n\n\n RANK ::::: ", rank)
                rank_value.update({
                    'rank': rank
                })
                # print("Rank value", rank_value)
                AllbidIdRank = request.env['bids.bids'].search([('tender_id', '=', bids_id.tender_id.id),
                                                                ('bids_top_rank', '>=', rank)])
                for bidIdRank in AllbidIdRank:
                    # print("\n\n\nbidIdRank", bidIdRank.bids_all_total)
                    # print("\nbidIdRank", bidIdRank.bids_top_rank)
                    bidIdRank.bids_top_rank = bidIdRank.bids_top_rank + 1
                    # print("\n\n\nbidIdRank", bidIdRank.bids_top_rank, '\n ******************************************')
                # print("\n\nbids_id============", bids_id)
                bids_id.bids_top_rank = rank
        return request.render("pragtech_tender_management.rank_template", rank_value)
