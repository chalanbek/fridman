"""
This code creates some test agent and registers until the user stops the process.
For this we wait for SIGINT.
"""
import logging
from sc_client.models import ScAddr, ScLinkContentType, ScTemplate, ScLinkContent, ScAddr, ScConstruction
from sc_client.constants import sc_types
from sc_client.client import template_search, get_links_by_content, create_elements_by_scs, create_elements, set_link_contents, get_link_content, delete_elements

from sc_kpm import ScAgentClassic, ScModule, ScResult, ScServer
from sc_kpm.sc_sets import ScSet
from sc_kpm.utils import (
    create_link,
    get_link_content_data,
    check_edge, create_edge,
    delete_edges,
    get_element_by_role_relation,
    get_element_by_norole_relation,
    get_system_idtf,
    get_edge
)
from sc_kpm.utils.action_utils import (
    create_action_answer,
    finish_action_with_status,
    get_action_arguments,
    get_element_by_role_relation
)
from sc_kpm import ScKeynodes

import json
import requests


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class AgentGetUserProfile(ScAgentClassic):
    def __init__(self):
        super().__init__("action_get_user_profile")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentGetUserProfile finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentGetUserProfile started")

        try:
            args = get_action_arguments(action_node, 1)
            user_id_addr = args[0]

            #nrel's
            self.nrel_data = {}
            nrel_data_index = ['nrel_surname', 'nrel_first_name', 'nrel_patronymic', 'nrel_grade', 'nrel_city',
                          'nrel_score_for_the_level_of_solved_problems', 'nrel_solution_scores', 'nrel_level_of_knowledge_of_topic', 
                          'nrel_solved_problems', 'nrel_not_solved_problems']
            for element in nrel_data_index: 
                self.nrel_data[element] = ScKeynodes.resolve(element, sc_types.NODE_CONST_NOROLE)

            #user node
            template = ScTemplate()
        
            template.triple_with_relation(
                    (sc_types.NODE_VAR, 'user'),
                    sc_types.EDGE_D_COMMON_VAR,
                    user_id_addr,
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    ScKeynodes.resolve('nrel_tg_id', sc_types.NODE_CONST_NOROLE),
                )

            results = template_search(template)
            result_search = results[0]
            self.user_addr = result_search.get('user')

            #statistics
            statistic_data = {}
            for element in nrel_data_index[:7]:
                statistic_data[f'{element[5:]}'] = get_link_content_data(self.call_temp(element))

            '''statistic_data['activity'] = self.triple_template_searching(
                    self.call_temp('nrel_activity', sctype=sc_types.NODE_VAR_TUPLE),
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    sc_types.LINK_VAR,
                    idtf='_activity'
                    )'''
            statistic_data['knowledge_level'] = {}
            template = ScTemplate()
            template.triple_with_relation(
                self.user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.EDGE_D_COMMON_VAR >> '_edgge',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                self.nrel_data['nrel_level_of_knowledge_of_topic']
            )
            results = template_search(template)
            nrel_main_idtf = ScKeynodes.resolve('nrel_main_idtf', sc_types.NODE_CONST_NOROLE)
            lang_ru = ScKeynodes.resolve("lang_en", sc_types.NODE_CONST_CLASS)
            for result in results:
                template1 = ScTemplate()
                template1.triple(
                sc_types.NODE_VAR >> '_topic',
                result.get('_edgge'),
                sc_types.LINK_VAR >> '_level',
                )
                res = template_search(template1)[0]
                link = res.get('_level')
                topic = res.get('_topic')

                template = ScTemplate()
                template.triple_with_relation(
                    topic,
                    sc_types.EDGE_D_COMMON_VAR,
                    sc_types.LINK_VAR >> 'link',
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_main_idtf
                )
                links = template_search(template)
                for link_ in links:
                    template = ScTemplate()
                    template.triple(
                        lang_ru,
                        sc_types.EDGE_ACCESS_VAR_POS_PERM,
                        link_.get('link') >> '_link'
                    )
                    if len(template_search(template)) != 0:
                        topic = get_link_content_data(template_search(template)[0].get('_link'))
                self.logger.info(f'{link}')
                link = get_link_content_data(link)
                self.logger.info('2')
                statistic_data['knowledge_level'][topic] = link

            for element in nrel_data_index[8:]:
                statistic_data[f'{element[5:]}'] = self.template_searching(
                    sc_types.NODE_VAR,
                    sc_types.EDGE_D_COMMON_VAR,
                    (sc_types.LINK_VAR, f'_{element[5:]}'),
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    self.call_temp(element, sctype=sc_types.NODE_VAR_TUPLE),
                    idtf=f'_{element[5:]}'
                    )

            construction = ScConstruction()
            
            text = str(json.dumps(statistic_data))
            construction.create_link(sc_types.LINK_CONST, ScLinkContent(text, ScLinkContentType.STRING))
            
            addrs = create_elements(construction)
            
            link_answer = addrs[0]
            
            
        except Exception as e:
            self.logger.info(f"AgentGetUserProfile: finished with an error {e}")
            return ScResult.ERROR

        create_action_answer(action_node, link_answer)
        return ScResult.OK

    def template_searching(self, *args, idtf='', find=False):
        template = ScTemplate()
        
        template.triple_with_relation(
            args[0],
            args[1],
            args[2],
            args[3],
            args[4]
        )

        results = template_search(template)
        if find:
            result_search = results[0]
            result = result_search.get(idtf)
            return result
        else:
            return len(results)
    
    def triple_template_searching(self, *args, idtf=''):
        template = ScTemplate()
        
        template.triple(
            args[0],
            args[1],
            (args[2], idtf)
        )

        results = template_search(template)
        result = []
        for link in results: result.append(get_link_content_data(link.get(idtf)))
        return result
        
    def call_temp(self, nrel: str, sctype=sc_types.LINK_VAR, find_value=True):
        return self.template_searching(
            self.user_addr,
            sc_types.EDGE_D_COMMON_VAR,
            (sctype, nrel[5:]),
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            self.nrel_data[nrel],
            idtf=nrel[5:],
            find=find_value
            )