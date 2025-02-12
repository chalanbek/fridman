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
            args = get_action_arguments(action_node, 2)
            user_addr = args[0]
            problem_addr = args[1]
            rrel_problem_topic = ScKeynodes.resolve('rrel_problem_topic', sc_types.NODE_CONST_ROLE)
            rrel_problem_first_topic = ScKeynodes.resolve('rrel_problem_first_topic', sc_types.NODE_CONST_ROLE)
            nrel_user = ScKeynodes.resolve('nrel_user', sc_types.NODE_CONST_NOROLE)
            nrel_level_of_knowledge_of_topic = ScKeynodes.resolve('nrel_level_of_knowledge_of_topic', sc_types.NODE_CONST_NOROLE)
            nrel_grade = ScKeynodes.resolve('nrel_grade', sc_types.NODE_CONST_NOROLE)
            nrel_level_within_grade = ScKeynodes.resolve('nrel_level_within_grade', sc_types.NODE_CONST_NOROLE)
            nrel_grade_comlexity_level = ScKeynodes.resolve('nrel_grade_comlexity_level', sc_types.NODE_CONST_NOROLE)
            nrel_experience = ScKeynodes.resolve('nrel_experience', sc_types.NODE_CONST_NOROLE)
            nrel_rating = ScKeynodes.resolve('nrel_rating', sc_types.NODE_CONST_NOROLE)
            complexity_knowledge_difference_min = 11

            if not user_addr.is_valid():
                self.logger.error('AgentUpdateStatistics: there are no argument with user')
                return ScResult.ERROR
            if not problem_addr.is_valid():
                self.logger.error('AgentUpdateStatistics: there are no argument with problem')
                return ScResult.ERROR
            
            self.logger.info('0')

            template = ScTemplate()
            template.triple_with_relation(
                sc_types.NODE_VAR >> '_topic',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                problem_addr,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                rrel_problem_first_topic
            )
            topic = template_search(template)[0].get('_topic')

            self.logger.info('1')

            template = ScTemplate()
            template.triple_with_relation(
                user_addr, 
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.EDGE_D_COMMON_VAR >> '_pair_topic_level',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_level_of_knowledge_of_topic
            )
            pair_topic_level_arr = template_search(template)
            for pair_level in pair_topic_level_arr:
                pair_topic_level = pair_level.get('_pair_topic_level')
                template = ScTemplate()
                template.triple(
                    topic,
                    pair_topic_level,
                    (sc_types.LINK_VAR, '_knowledge_level')
                )
                is_this_topic = template_search(template)
                if len(is_this_topic) != 0:
                    knowledge_level_addr = is_this_topic[0].get('_knowledge_level')
                    knowledge_level = float(get_link_content_data(knowledge_level_addr))
                    break
            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                (sc_types.LINK_VAR, '_user_grade'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_grade
            )
            user_grade_addr = template_search(template)[0].get('_user_grade')
            user_grade = float(get_link_content_data(user_grade_addr))

            template = ScTemplate()
            template.triple_with_relation(
                problem_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.EDGE_D_COMMON_VAR >> '_grade_level_pair',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_level_within_grade
            )
            complexities = template_search(template)

            for complexity in complexities:
                grade_level_pair_addr = complexity.get('_grade_level_pair')
                template = ScTemplate()
                template.triple_with_relation(
                    (sc_types.LINK_VAR, '_problem_grade'),
                    grade_level_pair_addr,
                    (sc_types.LINK_VAR, '_problem_grade_complexity'),
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_grade_comlexity_level
                )
                problem_grade_addr = template_search(template)[0].get('_problem_grade')
                problem_grade = float(get_link_content_data(problem_grade_addr))
                problem_grade_complexity_addr = template_search(template)[0].get('_problem_grade_complexity')
                problem_grade_complexity = float(get_link_content_data(problem_grade_complexity_addr))
                complexity_knowledge_difference = abs(user_grade - problem_grade)
                if(complexity_knowledge_difference < complexity_knowledge_difference_min):
                    complexity_knowledge_difference_min = complexity_knowledge_difference
                    complexity_level = problem_grade_complexity

            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> '_experience',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_experience
            )
            experience_addr = template_search(template)[0].get('_experience')
            experience = float(get_link_content_data(experience_addr))

            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> '_rating',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_rating
            )
            rating_addr = template_search(template)[0].get('_rating')
            rating = float(get_link_content_data(rating_addr))

            
            problem_count_coefficient = 20.0
            knowledge_level_coefficient = 2.0
            experience_coefficient = 1.0
            rating_coefficient = 20.0
            knowledge_level_rounded = round(knowledge_level)
            
            experience = experience + complexity_level * experience_coefficient
            rating = rating + (1/problem_count_coefficient)*(knowledge_level_coefficient**(complexity_level-knowledge_level_rounded))*rating_coefficient
            

            
            link_content3 = ScLinkContent(experience, ScLinkContentType.FLOAT, experience_addr)
            status = set_link_contents(link_content3)
            link_content4 = ScLinkContent(rating, ScLinkContentType.FLOAT, rating_addr)
            status = set_link_contents(link_content4)

        except Exception as e:
            self.logger.info(f"AgentUpdateStatistics: finished with an error {e}")
            return ScResult.ERROR

        return ScResult.OK
    
    """
    """