"""
This code creates some test agent and registers until the user stops the process.
For this we wait for SIGINT.
"""
import logging
from sc_client.models import ScAddr, ScLinkContentType, ScTemplate, ScLinkContent, ScConstruction
from sc_client.constants import sc_types
from sc_client.client import template_search, get_links_by_content, set_link_contents, create_elements, delete_elements

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


class AgentUpdateUserKnowledgeLevel(ScAgentClassic):
    def __init__(self):
        super().__init__("action_update_user_knowledge_level")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentUpdateUserKnowledgeLevel finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentUpdateUserKnowledgeLevel started")

        try:
            user_addr = get_action_arguments(action_node, 1)[0]
            task_addr = get_action_arguments(action_node, 2)[0]
            if not user_addr.is_valid():
                self.logger.error('AgentUpdateUserKnowledgeLevel: there are no argument with user')
                return ScResult.ERROR
            if not task_addr.is_valid():
                self.logger.error('AgentUpdateUserKnowledgeLevel: there are no argument with task')
                return ScResult.ERROR
            
            nrel_user = ScKeynodes.resolve('nrel_user', sc_types.NODE_CONST_NOROLE)
            nrel_level_of_knowledge_of_topic = ScKeynodes.resolve('nrel_level_of_knowledge_of_topic', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                user_addr, 
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.EDGE_D_COMMON_VAR >> '_pair_topic_level',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_level_of_knowledge_of_topic
            )

            results = template_search(template)
            result = results[0]
            pair_topic_level_addr = result.get('_pair_topic_level')

            rrel_problem_topic = ScKeynodes.resolve('rrel_problem_topic', sc_types.NODE_CONST_NOROLE)

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
                pair_topic_level_addr,
                sc_types.NODE_VAR >> '_knowledge_level'
            )
            results = template_search(template) 
            result = results[0]
            knowledge_level_addr = result.get('_knowledge_level')
            knowledge_level = get_link_content_data(knowledge_level_addr)

            nrel_level_within_grade = ScKeynodes.resolve('nrel_level_within_grade', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                task_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.EDGE_D_COMMON_VAR >> '_grade_level_pair',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_level_within_grade
            )

            results = template_search(template)
            result = results[0]
            grade_level_pair_addr = result.get('_grade_level_pair')

            nrel_grade = ScKeynodes.resolve('nrel_grade', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> '_user_grade',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_grade
            )

            results = template_search(template)
            result = results[0]
            user_grade_link = result.get('_user_grade')
            user_grade = get_link_content_data(user_grade_link)

            nrel_grade_complexity_level = ScKeynodes.resolve('nrel_grade_complexity_level', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                user_grade,
                grade_level_pair_addr,
                sc_types.LINK_VAR >> '_complexity_level',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_grade_complexity_level
            )

            results = template_search(template)
            result = results[0]
            complexity_level_link = result.get('_complexity_level')
            complexity_level = get_link_content_data(complexity_level_link)

            task_count_coefficient = 20.0
            knowledge_level_coefficient = 2.0
            knowledge_level_rounded = round(knowledge_level)
            
            nrel_solved_problems = ScKeynodes.resolve('nrel_solved_problems', sc_types.NODE_CONST_NOROLE)
            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                (sc_types.NODE_VAR_TUPLE, '_solved'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_solved_problems
            )
            results = template_search(template)
            result = results[0]
            solved_problems_addr = result.get('_solved')

            nrel_not_solved_problems = ScKeynodes.resolve('nrel_not_solved_problems', sc_types.NODE_CONST_NOROLE)
            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                (sc_types.NODE_VAR_TUPLE, '_not_solved'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_not_solved_problems
            )
            results = template_search(template)
            result = results[0]
            not_solved_problems_addr = result.get('_not_solved')
             
            template = ScTemplate()
            template.triple_with_relation(
                task_addr,
                sc_types.EDGE_D_COMMON_VAR,
                (sc_types.LINK_VAR, '_attempts'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                not_solved_problems_addr
            )
            results = template_search(template)

            template1 = ScTemplate()
            template1.triple_with_relation(
                task_addr,
                sc_types.EDGE_D_COMMON_VAR,
                (sc_types.LINK_VAR, '_attempts1'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                solved_problems_addr
            )
            results1 = template_search(template1)

            nrel_problem_for_which_level_is_reduced = ScKeynodes.resolve('nrel_problem_for_which_level_is_reduced', sc_types.NODE_CONST_NOROLE)
            template2 = ScTemplate()
            template2.triple_with_relation(
                knowledge_level_addr,
                (sc_types.EDGE_D_COMMON_VAR, 'level_problem_edge_'),
                task_addr,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_problem_for_which_level_is_reduced
            )
            results2 = template_search(template2)

            if len(results1) == 1:
                knowledge_level = knowledge_level + (1/task_count_coefficient)*(knowledge_level_coefficient**(complexity_level-knowledge_level_rounded))
                if len(results2) == 1:
                    result2 = results2[0]
                    level_problem_edge = result2.get('level_problem_edge_')
                    delete_elements(level_problem_edge)
            elif len(results) == 1 and knowledge_level_rounded >= complexity_level and len(results2) == 0:
                knowledge_level = knowledge_level - (1/task_count_coefficient)*(knowledge_level_coefficient**(knowledge_level_rounded-complexity_level))
                construction = ScConstruction()
                construction.create_edge(sc_types.EDGE_D_COMMON_CONST, knowledge_level_addr, task_addr, 'level_task_edge')
                construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_problem_for_which_level_is_reduced, 'level_task_edge')
                addrs = create_elements(construction)
                if len(addrs) == 2:
                    return ScResult.OK
                else:
                    raise
            

            """
            knowledge_level = knowledge_level + (1/task_count_coefficient)*(knowledge_level_coefficient**(complexity_level-knowledge_level_rounded))
            knowledge_level = knowledge_level - (1/task_count_coefficient)*(knowledge_level_coefficient**(knowledge_level_rounded-complexity_level))
            """
            
            link_content2 = ScLinkContent(knowledge_level, ScLinkContentType.FLOAT, knowledge_level_addr)
            set_link_contents(link_content2)

        except Exception as e:
            self.logger.info(f"AgentUpdateUserKnowledgeLevel: finished with an error {e}")
            return ScResult.ERROR

        return ScResult.OK