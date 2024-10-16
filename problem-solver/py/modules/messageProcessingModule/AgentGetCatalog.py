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
import json

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s", datefmt="[%d-%b-%y %H:%M:%S]"
)


class AgentGetCatalog(ScAgentClassic):
    def __init__(self):
        super().__init__("action_get_catalog")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentGetCatalogProblems finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentGetCatalogProblems started")

        try:
            topic_addr = get_action_arguments(action_node, 1)[0]
            if not topic_addr.is_valid():
                self.logger.error('AgentGetCatalogProblems: there are no argument with user')
                return ScResult.ERROR
            
            concept_math_topic = ScKeynodes.resolve('concept_math_topic', sc_types.NODE_CONST_CLASS)
            nrel_subtopic = ScKeynodes.resolve('nrel_subtopic', sc_types.NODE_CONST_NOROLE)
            nrel_subtopic_sequence = ScKeynodes.resolve('nrel_subtopic_sequence', sc_types.NODE_CONST_NOROLE)

            template = ScTemplate()
            template.triple(
                concept_math_topic,
                sc_types.EDGE_ACCESS_VAR_POS_PERM >> '_final_topic_edge',
                topic_addr
            )
            is_final_topic = template_search(template)
            if len(is_final_topic) == 0:
                self.logger.info('Thats not final subtopic')
                template = ScTemplate()
                template.triple_with_relation(
                    topic_addr,
                    sc_types.EDGE_D_COMMON_VAR,
                    sc_types.NODE_VAR >> '_topic',
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_subtopic
                )
                topics = template_search(template)
                for topic in topics:
                    topic_this = topic.get('_topic')
                    template = ScTemplate()
                    template.triple_with_relation(
                        topic_addr,
                        (sc_types.EDGE_D_COMMON_VAR, '_topic_this_arc'),
                        topic_this,
                        sc_types.EDGE_ACCESS_VAR_POS_PERM,
                        nrel_subtopic
                    )
                    topic_this_arc = template_search(template)[0].get('_topic_this_arc')
                    template = ScTemplate()
                    template.triple_with_relation(
                        sc_types.EDGE_D_COMMON_VAR,
                        (sc_types.EDGE_D_COMMON_VAR, '_topic_squence_arc'),
                        topic_this_arc,
                        sc_types.EDGE_ACCESS_VAR_POS_PERM,
                        nrel_subtopic_sequence
                    )
                    if len(template_search(template)) == 0:
                        topic_sequence_current = topic_this
                        break
                topic_list = []
                for topic in topics:
                    topic_list.append(topic_sequence_current)
                    template = ScTemplate()
                    template.triple_with_relation(
                        topic_sequence_current,
                        sc_types.EDGE_D_COMMON_VAR,
                        (sc_types.NODE_VAR, '_topic_next'),
                        sc_types.EDGE_ACCESS_VAR_POS_PERM,
                        nrel_subtopic_sequence
                    )
                    topic_next = template_search(template)[0].get('_topic_next')
                    topic_sequence_current = topic_next
                    ## вроде так, но надо проверить
                data = {1:topic_list}
                text = str(json.dumps(data))
                create_action_answer(action_node, text)
                return ScResult.OK
            else:
                return ScResult.ERROR
            

        except Exception as e:
            self.logger.info(f"AgentGetCatalogProblems: finished with an error {e}")
            return ScResult.ERROR