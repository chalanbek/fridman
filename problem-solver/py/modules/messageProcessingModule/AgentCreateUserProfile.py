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

import requests


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class AgentCreateUserProfile(ScAgentClassic):
    def __init__(self):
        super().__init__("action_create_user_profile")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentCreateUserProfile finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentCreateUserProfile started")

        try:
            link_data = []
            data_index = ['surname', 'firstname', 'patronymic', 'grade', 'city', 'id', 'level']
            args = get_action_arguments(action_node, 7)
            for i in range(len(args)-1): 
                link_data.append(args[i])
            
            level = get_link_content(args[-1])[0].data

            nrel_data = {}
            nrel_data_index = ['nrel_surname', 'nrel_first_name', 'nrel_patronymic', 'nrel_grade', 'nrel_city', 'nrel_tg_id',
                          'nrel_rating', 'nrel_experience', 'nrel_activity', 'nrel_statistics', 
                          'nrel_solved_problems', 'nrel_not_solved_problems']
            for element in nrel_data_index: 
                nrel_data[element] = ScKeynodes.resolve(element, sc_types.NODE_CONST_NOROLE)
            
            concept_data = {}
            data_index = ['concept_student', 'concept_user', 'concept_view_profile', 
                          'concept_achievements', 'concept_rating', 'concept_experience', 'concept_tg_id',
                          'concept_first_topic']
            for element in data_index: 
                concept_data[element] = ScKeynodes.resolve(element, sc_types.NODE_CONST_CLASS)

            tg_id = get_link_content_data(link_data[-1])
            [links_with_tg_id] = get_links_by_content(tg_id)
            for id in links_with_tg_id:
                if check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, concept_data['concept_tg_id'], id):
                    self.logger.info(f"AgentCreateUserProfile: the profile with such id is already existing")
                    return ScResult.ERROR
            
            construction = ScConstruction()
            #nodes, classes
            construction.create_node(sc_types.NODE_CONST, 'user')
            construction.create_node(sc_types.NODE_CONST, 'view_profile')
            construction.create_node(sc_types.NODE_CONST_TUPLE, 'achievements')
            construction.create_node(sc_types.NODE_CONST_TUPLE, 'solved_problems')
            construction.create_node(sc_types.NODE_CONST_TUPLE, 'not_solved_problems')
            construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'user', 'view_profile', 'view_profile_user')
            construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'user', 'achievements', 'achievements_user')
            construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'user', 'solved_problems', 'nrel_solved_problems_user')
            construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'user', 'not_solved_problems', 'nrel_not_solved_problems_user')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_data['concept_student'], 'user')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_data['concept_user'], 'user')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_data['concept_view_profile'], 'view_profile')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_data['concept_achievements'], 'achievements')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_data['nrel_statistics'], 'view_profile_user')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_data['nrel_activity'], 'achievements_user')
            nrel_data_index.remove('nrel_statistics')
            nrel_data_index.remove('nrel_activity')

            #links
            for i, el in enumerate(link_data):
                construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'user', el, f'{nrel_data_index[i]}_user')
                
            construction.create_link(sc_types.LINK_CONST, ScLinkContent(0, ScLinkContentType.INT), 'nrel_experience')
            construction.create_link(sc_types.LINK_CONST, ScLinkContent(0, ScLinkContentType.INT), 'score_for_the_level_of_solved_problems_user')
            construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'user', 'nrel_experience', 'nrel_experience_user')
            construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'user', 'score_for_the_level_of_solved_problems_user', 'nrel_rating_user')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_data['concept_rating'], 'score_for_the_level_of_solved_problems_user')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_data['concept_experience'], 'nrel_experience')
            
            template = ScTemplate()
            template.triple(
                concept_data['concept_first_topic'],
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                (sc_types.NODE_VAR, 'topic')
            )

            nrel_level_of_knowledge_of_topic = ScKeynodes.resolve('nrel_level_of_knowledge_of_topic', sc_types.NODE_CONST_NOROLE)
            res = template_search(template)
            for i, element in enumerate(res):
                construction.create_link(sc_types.LINK_CONST, ScLinkContent(level, ScLinkContentType.INT), f'link_{i}')
                construction.create_edge(sc_types.EDGE_D_COMMON_CONST, element.get('topic'), f'link_{i}', f'pair_{i}')
                construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'user', f'pair_{i}', f'_pair_{i}')
                construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_level_of_knowledge_of_topic, f'_pair_{i}')

            #nrels
            for el in nrel_data_index:
                construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_data[el], f'{el}_user')

            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, concept_data['concept_tg_id'], link_data[-1])
            addrs = create_elements(construction)

            '''if len(addrs) != 27:
                raise'''
            
            return ScResult.OK
        except Exception as e:
            self.logger.info(f"AgentCreateUserProfile: finished with an error {e}")
            return ScResult.ERROR