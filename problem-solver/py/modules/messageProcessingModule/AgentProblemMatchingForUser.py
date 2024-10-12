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


class AgentProblemMatchingForUser(ScAgentClassic):
    def __init__(self):
        super().__init__("action_problem_matching_for_user")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentProblemMatchingForUser finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentProblemMatchingForUser started")

        try:
            user_addr = get_action_arguments(action_node, 1)[0]
            args = get_action_arguments(action_node, 2)
            user_addr = args[0]
            user_lowest_knowledge_level = 7.0
            is_problem_matched = 0
            nrel_level_of_knowledge_of_topic = ScKeynodes.resolve('nrel_level_of_knowledge_of_topic', sc_types.NODE_CONST_NOROLE)
            nrel_grade = ScKeynodes.resolve('nrel_grade', sc_types.NODE_CONST_NOROLE)
            rrel_problem_topic = ScKeynodes.resolve('rrel_problem_topic', sc_types.NODE_CONST_ROLE)
            nrel_level_within_grade = ScKeynodes.resolve('nrel_level_within_grade', sc_types.NODE_CONST_NOROLE)
            nrel_grade_comlexity_level = ScKeynodes.resolve('nrel_grade_comlexity_level', sc_types.NODE_CONST_NOROLE)
            nrel_problem_number = ScKeynodes.resolve('nrel_problem_number', sc_types.NODE_CONST_NOROLE)
            nrel_problem_text = ScKeynodes.resolve('nrel_problem_text', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> '_user_grade',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_grade
            )
            results = template_search(template)
            user_grade_addr = results[0].get('_user_grade')
            user_grade = get_link_content_data(user_grade_addr)

            if not user_addr.is_valid():
                self.logger.error('AgentProblemMatchingForUser: there are no argument with user')
                return ScResult.ERROR
            

            template = ScTemplate()
            template.triple_with_relation(
                user_addr,
                sc_types.EDGE_D_COMMON_VAR,
                (sc_types.EDGE_D_COMMON_VAR, '_pair_topic_level'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_level_of_knowledge_of_topic
            )
            results = template_search(template)
            for result in results:
                pair_topic_level_addr = result.get('_pair_topic_level')
                template = ScTemplate()
                template.triple(
                    (sc_types.NODE_VAR, '_topic'),
                    pair_topic_level_addr,
                    (sc_types.LINK_VAR, '_topic_knowledge_level')
                )
                pairs = template_search(template)
                topic_knowledge_level_addr = pairs[0].get('_topic_knowledge_level')
                topic_knowledge_level = float(get_link_content_data(topic_knowledge_level_addr))
                topic_addr = pairs[0].get('_topic')
                if topic_knowledge_level < user_lowest_knowledge_level:
                    user_lowest_knowledge_level = topic_knowledge_level_addr
                    lowest_level_topic_addr = topic_addr
            template = ScTemplate()
            template.triple_with_relation(
                lowest_level_topic_addr,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                (sc_types.NODE_VAR, '_problem'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                rrel_problem_topic
            )
            problems = template_search(template)
            for problem in problems:
                this_problem = problem.get('_problem')
                template = ScTemplate()
                template.triple_with_relation(
                    this_problem,
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
                    problem_grade = get_link_content_data(problem_grade_addr)
                    problem_grade_complexity_addr = template_search(template)[0].get('_problem_grade_complexity')
                    problem_grade_complexity = get_link_content_data(problem_grade_complexity_addr)
                    if problem_grade == user_grade & problem_grade_complexity == round(user_lowest_knowledge_level):
                        is_problem_matched = 1
                        matched_problem = this_problem
                        template = ScTemplate()
                        template.triple_with_relation(
                            this_problem,
                            sc_types.EDGE_D_COMMON_VAR,
                            (sc_types.NODE_VAR, '_problem_number'),
                            sc_types.EDGE_ACCESS_VAR_POS_PERM,
                            nrel_problem_number
                        )
                        problem_number_link = template_search(template)[0].get('_problem_number')
                        problem_number = get_link_content_data(problem_number_link)
                        break
                else: break
            if is_problem_matched ==0:
                for problem in problems:
                    this_problem = problem.get('_problem')
                    template = ScTemplate()
                    template.triple_with_relation(
                        this_problem,
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
                        problem_grade = get_link_content_data(problem_grade_addr)
                        problem_grade_complexity_addr = template_search(template)[0].get('_problem_grade_complexity')
                        problem_grade_complexity = get_link_content_data(problem_grade_complexity_addr)
                        if problem_grade == user_grade & problem_grade_complexity <= round(user_lowest_knowledge_level):
                            is_problem_matched = 1
                            template = ScTemplate()
                            template.triple_with_relation(
                                this_problem,
                                sc_types.EDGE_D_COMMON_VAR,
                                (sc_types.NODE_VAR, '_problem_number'),
                                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                                nrel_problem_number
                            )
                            problem_number_link = template_search(template)[0].get('_problem_number')
                            problem_number = get_link_content_data(problem_number_link)
                            break
                        else: break
            if is_problem_matched == 0:
                print('Приносим свои извинения, на данный момент не получается подобрать задачу. Попробуйте перейти в каталог и выбрать задачу там.')
            else: 
                template = ScTemplate()
                template.triple_with_relation(
                    matched_problem,
                    sc_types.EDGE_D_COMMON_VAR,
                    (sc_types.NODE_VAR, '_problem_text'),
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_problem_text
                )
                problem_text_link = template_search(template)[0].get('_problem_text')
                problem_text = get_link_content_data(problem_text_link)
                print('(', problem_number, ')\n', problem_text)




        except Exception as e:
            self.logger.info(f"AgentProblemMatchingForUser: finished with an error {e}")
            return ScResult.ERROR

        return ScResult.OK