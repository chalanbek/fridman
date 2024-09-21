"""
This code creates some test agent and registers until the user stops the process.
For this we wait for SIGINT.
"""
import logging
from sc_client.models import ScAddr, ScLinkContentType, ScTemplate
from sc_client.constants import sc_types
from sc_client.client import template_search, get_links_by_content

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


class AgentUpdateStatistics(ScAgentClassic):
    def __init__(self):
        super().__init__("action_update_statistics")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentUpdateStatistics finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentUpdateStatistics started")

        try:
            user_addr = get_action_arguments(action_node, 1)[0]
            task_addr = get_action_arguments(action_node, 2)[0]
            if not user_addr.is_valid():
                self.logger.error('AgentUpdateStatistics: there are no argument with user')
                return ScResult.ERROR
            if not task_addr.is_valid():
                self.logger.error('AgentUpdateStatistics: there are no argument with task')
                return ScResult.ERROR
            
            nrel_user = ScKeynodes.resolve('nrel_user', sc_types.NODE_CONST_NOROLE)
            nrel_level_of_knowledge_of_topic = ScKeynodes.resolve('nrel_level_of_knowledge_of_topic', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                user_addr, 
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.EDGE_D_COMMON_VAR >> '_pair_theme_level',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_level_of_knowledge_of_topic
            )

            results = template_search(template)
            result = results[0]
            pair_theme_level_addr = result.get('_pair_theme_level')

            template = ScTemplate()
            template.triple_with_relation(
                sc_types.NODE_VAR >> '_topic',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                task_addr,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                rrel_problem_topic
            )

            results = template_search(template)
            result = results[0]
            topic_addr = result.get('_topic')

            template = ScTemplate()
            template.triple(
                topic_addr,
                pair_theme_level_addr,
                sc_types.NODE_VAR >> '_knowledge_level'
            )
            results = template_search(template) 
            result = results[0]
            knowledge_level_link = result.get('_knowledge_level')
            knowledge_level = get_link_content_data(knowledge_level_link)

            template = ScTemplate()
            template.triple_with_relation(
                task_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> '_complexity_level',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_complexity_level
            )
            results = template_search(template)
            result = results[0]
            complexity_level_link = result.get('_complexity_level')
            complexity_level = get_link_content_data(complexity_level_link)

            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> '_experience',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_solution_scores
            )
            results = template_search(template)
            result = results[0]
            experience_link = result.get('_experience')
            experience = get_link_content_data(experience_link)

            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> '_rating',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_score_for_the_level_of_solved_problems
            )
            results = template_search(template)
            result = results[0]
            rating_link = result.get('_rating')
            rating = get_link_content_data(rating_link)

            
            task_count_coefficient = 20.0
            knowledge_level_coefficient = 2.0
            experience_coefficient = 1.0
            rating_coefficient = 20.0
            knowledge_level_rounded = round(knowledge_level)
            """
            experience = experience + complexity_level * experience_coefficient
            rating = rating + (1/task_count_coefficient)*(knowledge_level_coefficient**(complexity_level-knowledge_level_rounded))*rating_coefficient
            """

            
            link_content3 = ScLinkContent(experience, ScLinkContentType.FLOAT, experience_link)
            status = set_link_contents(link_content3)
            ink_content4 = ScLinkContent(rating, ScLinkContentType.FLOAT, rating_link)
            status = set_link_contents(link_content4)

        except Exception as e:
            self.logger.info(f"AgentUpdateStatistics: finished with an error {e}")
            return ScResult.ERROR

        return ScResult.OK
    
    """
    """