"""
This code creates some test agent and registers until the user stops the process.
For this we wait for SIGINT.
"""
import logging
from sc_client.models import ScAddr, ScLinkContentType, ScTemplate, ScConstruction
from sc_client.constants import sc_types
from sc_client.client import template_search, get_links_by_content, create_elements

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


class AgentGetSolutionAnswer(ScAgentClassic):
    def __init__(self):
        super().__init__("action_get_solution_answer")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentGetSolutionAnswer finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentGetSolutionAnswer started")

        try:
            args = get_action_arguments(action_node, 2)
            problem_number_link_addr = args[0]
            user_id_addr = args[1]

            if not problem_number_link_addr.is_valid():
                self.logger.error('AgentGetSolutionAnswer: there are no argument with problem number')
                return ScResult.ERROR
            
            problem_number = get_link_content_data(problem_number_link_addr)
            [links_with_problem_number] = get_links_by_content(problem_number)
            if len(links_with_problem_number) == 0:
                self.logger.error('AgentGetSolutionAnswer: there are no problems with such problem number')
                return ScResult.ERROR

            concept_problem_number = ScKeynodes.resolve('concept_problem_number', sc_types.NODE_CONST_CLASS)
            problem_number_links = []
            for problem_number_link_addr in links_with_problem_number:
                if check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, concept_problem_number, problem_number_link_addr):
                    problem_number_links.append(problem_number_link_addr)

            if len(problem_number_links) == 0:
                self.logger.error('AgentGetSolutionAnswer: there are no problem links with such problem number')
                return ScResult.ERROR
            elif len(problem_number_links) > 1:
                self.logger.error('AgentGetSolutionAnswer: there are more than 1 problem with such problem number')
                return ScResult.ERROR
            
            nrel_problem_number = ScKeynodes.resolve('nrel_problem_number', sc_types.NODE_CONST_NOROLE)
            problem_number_link_addr = problem_number_links[0]
            template = ScTemplate()
            template.triple_with_relation(
                (sc_types.NODE_VAR, '_problem'),
                sc_types.EDGE_D_COMMON_VAR,
                problem_number_link_addr,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_problem_number
            )

            results = template_search(template)
            if len(results) == 0:
                self.logger.error('AgentGetSolutionAnswer: there are no problems with such problem number')
                return ScResult.ERROR
            
            result = results[0]
            problem_addr = result.get('_problem')

            nrel_solution_answer = ScKeynodes.resolve('nrel_solution_answer', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                problem_addr,
                sc_types.EDGE_D_COMMON_VAR,
                (sc_types.LINK_VAR, '_nrel_solution_answer'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_solution_answer
            )

            results = template_search(template)
            if len(results) == 0:
                self.logger.error('AgentGetSolutionAnswer: there are no text problem with such problem number')
                return ScResult.ERROR

            result = results[0]
            nrel_solution_answer_addr = result.get('_nrel_solution_answer')

        except Exception as e:
            self.logger.info(f"AgentGetSolutionAnswer: finished with an error {e}")
            return ScResult.ERROR

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
        user_addr = result_search.get('user')

        template = ScTemplate()
        template.triple_with_relation(
            user_addr,
            sc_types.EDGE_D_COMMON_VAR,
            (sc_types.NODE_VAR_TUPLE, '_solved'),
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            ScKeynodes.resolve('nrel_solved_problems', sc_types.NODE_CONST_NOROLE)
        )
        results = template_search(template)
        result = results[0]
        solved_problems_addr = result.get('_solved')
        template1 = ScTemplate()
        template1.triple_with_relation(
            problem_addr,
            sc_types.EDGE_D_COMMON_VAR,
            (sc_types.LINK_VAR, '_attempts1'),
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            solved_problems_addr
        )

        results1 = template_search(template1)
        
        nrel_saw_answer = ScKeynodes.resolve('nrel_saw_answer', sc_types.NODE_CONST_NOROLE)
        template3 = ScTemplate()
        template3.triple_with_relation(
            user_addr,
            sc_types.EDGE_D_COMMON_VAR,
            problem_addr,
            sc_types.EDGE_ACCESS_VAR_POS_PERM,
            nrel_saw_answer
        )

        results3 = template_search(template3)

        if len(results1) == 0 and len(results3) == 0:
            construction = ScConstruction()
            
            construction.create_edge(sc_types.EDGE_D_COMMON_CONST, user_addr, problem_addr, 'user_problem_edge')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_saw_answer, 'user_problem_edge')
            addrs = create_elements(construction)
            if len(addrs) != 2:
                self.logger.error('AgentGetSolutionAnswer: something wrong with creating edge')
                return ScResult.ERROR
        
        create_action_answer(action_node, nrel_solution_answer_addr)
        return ScResult.OK
    