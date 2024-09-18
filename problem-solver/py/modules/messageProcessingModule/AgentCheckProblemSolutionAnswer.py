"""
This code creates some test agent and registers until the user stops the process.
For this we wait for SIGINT.
"""
import logging
from sc_client.models import ScAddr, ScLinkContentType, ScTemplate, SCs, ScConstruction
from sc_client.constants import sc_types
from sc_client.client import template_search, get_links_by_content, create_elements_by_scs, create_elements

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


class AgentCheckProblemSolutionAnswer(ScAgentClassic):
    def __init__(self):
        super().__init__("action_check_problem_solution_answer")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentCheckProblemSolutionAnswer finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentCheckProblemSolutionAnswer started")

        try:
            args = get_action_arguments(action_node, 3)
            problem_addr = args[0]
            user_problem_solution_answer_addr = args[1]
            user_addr = args[2]

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
            
            if not problem_addr.is_valid() or not user_problem_solution_answer_addr.is_valid() or not user_addr.is_valid(): 
                self.logger.error('AgentCheckProblemSolutionAnswer: there are no one of argument')
                return ScResult.ERROR
            
            user_problem_solution_answer = str(get_link_content_data(user_problem_solution_answer_addr)).split(',')

            nrel_solution_answer = ScKeynodes.resolve('nrel_solution_answer', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                problem_addr,
                sc_types.EDGE_D_COMMON_VAR,
                (sc_types.LINK_VAR, '_problem_solution_answer'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_solution_answer
            )

            results = template_search(template)
            if len(results) == 0:
                self.logger.error('AgentCheckProblemSolutionAnswer: there are no answer for this problem')
                return ScResult.ERROR

            result = results[0]
            problem_solution_answer = str(get_link_content_data(result.get('_problem_solution_answer'))).split(',')
            
            nrel_solution_attempts_number = ScKeynodes.resolve('nrel_solution_attempts_number', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple(
                not_solved_problems_addr,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                (sc_types.EDGE_D_COMMON_VAR, '_pair_problem_attempts_not_solved'),
            )

            results = template_search(template)
            if len(results) == 0:
                template1 = ScTemplate()
                template1.triple(
                solved_problems_addr,
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                (sc_types.EDGE_D_COMMON_VAR, '_pair_problem_attempts_solved'),
                )
                results1 = template_search(template1)
                if len(results1) == 0:
                    if problem_solution_answer == user_problem_solution_answer:
                        '''construction = ScConstruction()  # Create output_struct for example
                        construction.create_link(sc_types.LINK_CONST)
                        output_struct = create_elements(construction)[0]
                        
                        res = create_elements_by_scs([SCs("problem => total_attempts;;", problem_addr, output_struct)])
                        assert results == [True, True]'''
                        #add the problem to solved, make the value of attempts "1", call the 3rd agent
                        return ScResult.OK
                    else:
                        #add the problem to not solved, make the value of attempts "1", call the 3rd agent
                        return ScResult.ERROR
                else:
                    for edge in results1:
                        template2 = ScTemplate()
                        template2.triple_with_relation(
                        problem_addr,
                        edge,
                        (sc_types.LINK_VAR, '_attempts'),
                        sc_types.EDGE_ACCESS_VAR_POS_PERM
                        nrel_solution_attempts_number
                        )
                        results2 = template_search(template1)
                        if len(results2) == 1:
                            result2 = results2[0]
                            attempts_addr = result2.get('_attempts')
                            break
                if problem_solution_answer == user_problem_solution_answer:
                    #plus "1" the total value of attempts (our attempts_addr), call the 3rd agent
                    return ScResult.OK
                else:
                    #plus "1" the total value of attempts (our attempts_addr), call the 3rd agent
                    return ScResult.ERROR
            else:
                for edge in results:
                    template1 = ScTemplate()
                    template1.triple_with_relation(
                    problem_addr,
                    edge,
                    (sc_types.LINK_VAR, '_attempts'),
                    sc_types.EDGE_ACCESS_VAR_POS_PERM
                    nrel_solution_attempts_number
                    )
                    results1 = template_search(template1)
                    if len(results2) == 1:
                        result1 = results1[0]
                        attempts_addr = result.get('_attempts')
                        break
                    if problem_solution_answer == user_problem_solution_answer:
                        #add the problem to solved, remove from not, plus "1" the total value of attempts (our attempts_addr), call the 3rd agent with meaning, that user solved the problem this time
                        return ScResult.OK
                    else:
                        #plus "1" the total value of attempts (our attempts_addr), call the 3rd agent
                        return ScResult.ERROR


            '''[links_with_problem_number] = get_links_by_content(problem_number)
            if len(links_with_problem_number) == 0:
                self.logger.error('AgentCheckProblemSolutionAnswer: there are no problems with such problem number')
                return ScResult.ERROR

            concept_problem_number = ScKeynodes.resolve('concept_problem_number', sc_types.NODE_CONST_CLASS)
            problem_number_links = []
            for problem_number_link_addr in links_with_problem_number:
                if check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, concept_problem_number, problem_number_link_addr):
                    problem_number_links.append(problem_number_link_addr)

            if len(problem_number_links) == 0:
                self.logger.error('AgentCheckProblemSolutionAnswer: there are no problem links with such problem number')
                return ScResult.ERROR
            elif len(problem_number_links) > 1:
                self.logger.error('AgentCheckProblemSolutionAnswer: there are more than 1 problem with such problem number')
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
                self.logger.error('AgentCheckProblemSolutionAnswer: there are no problems with such problem number')
                return ScResult.ERROR
            
            result = results[0]
            problem_addr = result.get('_problem')

            nrel_problem_text = ScKeynodes.resolve('nrel_problem_text', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                problem_addr,
                sc_types.EDGE_D_COMMON_VAR,
                (sc_types.LINK_VAR, '_problem_text'),
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_problem_text
            )

            results = template_search(template)
            if len(results) == 0:
                self.logger.error('AgentCheckProblemSolutionAnswer: there are no text problem with such problem number')
                return ScResult.ERROR

            result = results[0]
            problem_text_addr = result.get('_problem_text')'''

        except Exception as e:
            self.logger.info(f"AgentCheckProblemSolutionAnswer: finished with an error {e}")
            return ScResult.ERROR

        #create_action_answer(action_node, problem_text_addr)

        return ScResult.OK
        