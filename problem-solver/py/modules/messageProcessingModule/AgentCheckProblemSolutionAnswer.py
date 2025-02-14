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
            problem_number_link_addr = args[0]
            user_problem_solution_answer_addr = args[1]
            user_addr = args[2]

            #find the problem by its number
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
            ############################################################
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
            
            nrel_attempts = ScKeynodes.resolve('nrel_attempts', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple_with_relation(
                problem_addr,
                (sc_types.EDGE_D_COMMON_VAR, '_pair_problem_link'),
                (sc_types.LINK_VAR, '_attempts'),
                (sc_types.EDGE_ACCESS_VAR_POS_PERM,'_pair_not_solved_edge_'),
                not_solved_problems_addr
            )
            results = template_search(template)

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
            if len(results) == 0:
                template1 = ScTemplate()
                template1.triple_with_relation(
                    problem_addr,
                    sc_types.EDGE_D_COMMON_VAR,
                    (sc_types.LINK_VAR, '_attempts1'),
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    solved_problems_addr
                )

                results1 = template_search(template1)
                if len(results1) == 0:
                    #creating the structure
                    if len(results3) == 0:
                        construction = ScConstruction()
                        link_content = ScLinkContent(1, ScLinkContentType.INT)
                        construction.create_link(sc_types.LINK_CONST, link_content, 'link')

                        construction.create_edge(sc_types.EDGE_D_COMMON_CONST, problem_addr, 'link', 'problem_attempts_edge')
                        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, nrel_attempts, 'problem_attempts_edge')

                    if problem_solution_answer == user_problem_solution_answer and len(results3) == 0:
                        #add the problem to solved, make the value of attempts "1", call the 3rd agent
                        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, solved_problems_addr, 'problem_attempts_edge')
                        addrs = create_elements(construction)
                        if len(addrs) == 4:
                            self.call_agent_update_user_kowledge_level(user_addr=user_addr, problem_addr=problem_addr)
                            self.call_agent_update_statistics(user_addr=user_addr, problem_addr=problem_addr)
                            return ScResult.OK
                        else:
                            raise

                    elif problem_solution_answer == user_problem_solution_answer and len(results3) == 1:
                        return ScResult.OK
                    
                    elif problem_solution_answer != user_problem_solution_answer and len(results3) == 0:
                        #add the problem to not solved, make the value of attempts "1", call the 3rd agent
                        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, not_solved_problems_addr, 'problem_attempts_edge')
                        addrs = create_elements(construction)
                        if len(addrs) == 4:
                            self.call_agent_update_user_kowledge_level(user_addr=user_addr, problem_addr=problem_addr)
                            return ScResult.ERROR
                        else:
                            raise

                    elif problem_solution_answer != user_problem_solution_answer and len(results3) == 1:
                        return ScResult.ERROR
                    
                else:
                    result1 = results1[0]
                    attempts_addr = result1.get('_attempts1')
                    if problem_solution_answer == user_problem_solution_answer:
                        #plus "1" the total value of attempts (our attempts_addr)
                        self.update_link(attempts_addr=attempts_addr)
                        return ScResult.OK
                    else:
                        #plus "1" the total value of attempts (our attempts_addr)
                        self.update_link(attempts_addr=attempts_addr)
                        return ScResult.ERROR
            else:
                result = results[0]
                attempts_addr = result.get('_attempts')
                if problem_solution_answer == user_problem_solution_answer and len(results3) == 0:
                    #add the problem to solved, remove from not, plus "1" the total value of attempts (our attempts_addr), call the 3rd agent
                    self.update_link(attempts_addr=attempts_addr)

                    pair_not_solved_edge_ = result.get('_pair_not_solved_edge_')
                    pair_problem_link = result.get('_pair_problem_link')

                    delete_elements(pair_not_solved_edge_)

                    construction = ScConstruction()
                    construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, solved_problems_addr, pair_problem_link)
                    addrs = create_elements(construction)
                    if len(addrs) == 1:
                        self.call_agent_update_user_kowledge_level(user_addr=user_addr, problem_addr=problem_addr)
                        self.call_agent_update_statistics(user_addr=user_addr, problem_addr=problem_addr)
                        return ScResult.OK
                    else:
                        raise

                elif problem_solution_answer == user_problem_solution_answer and len(results3) == 1:
                    return ScResult.OK
                
                elif problem_solution_answer != user_problem_solution_answer and len(results3) == 0:
                    #plus "1" the total value of attempts (our attempts_addr), call the 3rd agent
                    self.update_link(attempts_addr=attempts_addr)
                    self.call_agent_update_user_kowledge_level(user_addr=user_addr, problem_addr=problem_addr)
                    return ScResult.ERROR
                
                elif problem_solution_answer != user_problem_solution_answer and len(results3) == 1:
                    return ScResult.ERROR
                
        except Exception as e:
            self.logger.info(f"AgentCheckProblemSolutionAnswer: finished with an error {e}")
            return ScResult.ERROR
        
    def update_link(self, attempts_addr):
        link_content = get_link_content(attempts_addr)[0]
        link_content2 = ScLinkContent(int(link_content.data)+1, ScLinkContentType.INT, attempts_addr)
        set_link_contents(link_content2)
    
    def call_agent_update_user_kowledge_level(self, user_addr, problem_addr):
        construction = ScConstruction()
        construction.create_node(sc_types.NODE_CONST, 'node')

        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, 'node', user_addr, 'user_edge')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, 'node', problem_addr,'problem_edge')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('rrel_1', sc_types.NODE_CONST_ROLE), 'user_edge')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('rrel_2', sc_types.NODE_CONST_ROLE), 'problem_edge')

        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('question', sc_types.NODE_CONST_CLASS), 'node')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('action_update_user_knowledge_level', sc_types.NODE_CONST_CLASS), 'node')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('question_initiated', sc_types.NODE_CONST_CLASS), 'node')

        addrs = create_elements(construction)
        if len(addrs) == 8:
            return ScResult.OK
        else:
            raise

    def call_agent_update_statistics(self, user_addr, problem_addr):
        construction = ScConstruction()
        construction.create_node(sc_types.NODE_CONST, 'node')

        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, 'node', user_addr, 'user_edge')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, 'node', problem_addr,'problem_edge')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('rrel_1', sc_types.NODE_CONST_ROLE), 'user_edge')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('rrel_2', sc_types.NODE_CONST_ROLE), 'problem_edge')

        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('question', sc_types.NODE_CONST_CLASS), 'node')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('action_update_statistics', sc_types.NODE_CONST_CLASS), 'node')
        construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('question_initiated', sc_types.NODE_CONST_CLASS), 'node')

        addrs = create_elements(construction)
        if len(addrs) == 8:
            return ScResult.OK
        else:
            raise