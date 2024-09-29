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
import numpy as np
import requests


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class AgentGetCatalogTheorems(ScAgentClassic):
    def __init__(self):
        super().__init__("action_get_catalog_theorems")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentGetCatalogTheorems finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentGetCatalogTheorems started")

        try:
            topic_addr = get_action_arguments(action_node, 1)[0]
            if not topic_addr.is_valid():
                self.logger.error('AgentGetCatalogTheorems: there are no argument with user')
                return ScResult.ERROR
            
            concept_math_topic = ScKeynodes.resolve('concept_math_topic', sc_types.NODE_CONST_CLASS)
            rrel_theorem_topic = ScKeynodes.resolve('rrel_theorem_topic', sc_types.NODE_CONST_ROLE)
            nrel_theorem_name = ScKeynodes.resolve('nrel_theorem_name', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple(
                concept_math_topic,
                sc_types.EDGE_ACCESS_VAR_POS_PERM >> '_final_topic_edge',
                topic_addr
            )
            is_final_topic = template_search(template)
            if len(is_final_topic) == 0:
                self.logger.info('Thats not final subtopic')
                """если это не последняя тема, вызывать потом этого же агента от этой темы"""
            else:
                template = ScTemplate()
                template.triple_with_relation(
                    topic_addr,
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    sc_types.NODE_VAR >> '_theorem',
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    rrel_theorem_topic
                )
                theorems = template_search(template)
                theorem_name_list = np.empty(len(theorems), dtype=np.str)
                theorem_i = 0
                for theorem in theorems:
                    theorem_this = theorem.get('_theorem')
                    template = ScTemplate()
                    template.triple_with_relation(
                        theorem_this,
                        sc_types.DGE_D_COMMON_VAR,
                        sc_types.LINK_VAR >> '_theorem_name',
                        sc_types.EDGE_ACCESS_VAR_POS_PERM,
                        nrel_theorem_name
                    )
                    names = template_search(template)
                    name = names[0]
                    name_link = name.get('_theorem_name')
                    theorem_name = get_link_content_data(name_link)
                    theorem_name_list[theorem_i] = theorem_name
                    theorem_i += 1
                theorem_name_list.sort()
                for theorem_number_count in theorem_name_list:
                    self.logger.info(f"{theorem_number_count}")

            

        except Exception as e:
            self.logger.info(f"AgentGetCatalogTheorems: finished with an error {e}")
            return ScResult.ERROR

        return ScResult.OK