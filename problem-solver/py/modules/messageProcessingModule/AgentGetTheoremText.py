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


class AgentGetTheoremText(ScAgentClassic):
    def __init__(self):
        super().__init__("action_get_theorem_text")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentGetTheoremText finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentGetTheoremText started")

        try:
            theorem_link_addr = get_action_arguments(action_node, 1)[0]

            if not theorem_link_addr.is_valid():
                self.logger.error('AgentGetTheoremText: there are no argument with theorem number')
                return ScResult.ERROR
            
            theorem = get_link_content_data(theorem_link_addr)
            [links_with_theorem] = get_links_by_content(theorem)
            if len(links_with_theorem) == 0:
                self.logger.error('AgentGetTheoremText: there are no theorems with such theorem number')
                return ScResult.ERROR
            
            nrel_theorem_name = ScKeynodes.resolve('nrel_theorem_name', sc_types.NODE_CONST_NOROLE)
            for link in links_with_theorem:
                template = ScTemplate()
                template.triple_with_relation(
                    sc_types.NODE_VAR >> '_theorem',
                    sc_types.EDGE_D_COMMON_VAR,
                    link,
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_theorem_name
                )
                links = template_search(template)
                if len(links) == 1:
                    theorem_addr = links[0].get('_theorem')
                    break

            nrel_theorem_definition = ScKeynodes.resolve('nrel_theorem_definition', sc_types.NODE_CONST_NOROLE)
            template = ScTemplate()
            template.triple_with_relation(
                theorem_addr,
                sc_types.EDGE_D_COMMON_VAR,
                sc_types.LINK_VAR >> '_theorem_def',
                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                nrel_theorem_definition
            )
            links = template_search(template)
            if len(links) == 0:
                self.logger.error('AgentGetTheoremText: there are no theorems with such theorem number1')
                return ScResult.ERROR
            theorem_text_addr = links[0].get('_theorem_def')
            
        except Exception as e:
            self.logger.info(f"AgentGetTheoremText: finished with an error {e}")
            return ScResult.ERROR

        create_action_answer(action_node, theorem_text_addr)

        return ScResult.OK
        