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


class AgentReceiveFeedback(ScAgentClassic):
    def __init__(self):
        super().__init__("action_receive_feedback")

    def on_event(self, event_element: ScAddr, event_edge: ScAddr, action_element: ScAddr) -> ScResult:
        result = self.run(action_element)
        is_successful = result == ScResult.OK
        finish_action_with_status(action_element, is_successful)
        self.logger.info("AgentReceiveFeedback finished %s",
                         "successfully" if is_successful else "unsuccessfully")
        return result

    def run(self, action_node: ScAddr) -> ScResult:
        self.logger.info("AgentReceiveFeedback started")

        try:
            args = get_action_arguments(action_node, 3)
            text_link = args[0]
            user_id_link = args[1]
            tg_id = get_link_content_data(user_id_link)
            concept_tg_id_ = ScKeynodes.resolve('concept_tg_id', sc_types.NODE_CONST_CLASS)
            [links_with_tg_id] = get_links_by_content(tg_id)
            for id in links_with_tg_id:
                if check_edge(sc_types.EDGE_ACCESS_VAR_POS_PERM, concept_tg_id_, id):
                    user_id_link = id
                    break
            else:
                raise
            concept_report_type = args[2]

            construction = ScConstruction()
            #creating relations between the user id and the feedback
            construction.create_node(sc_types.NODE_CONST, 'feedback')
            construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'feedback', user_id_link, 'sender_id')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('nrel_feedback_sender_tg_id', sc_types.NODE_CONST_NOROLE), 'sender_id')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM,  ScKeynodes.resolve('concept_feedback_sender_tg_id', sc_types.NODE_CONST_CLASS), user_id_link)
            
            #creating relations between the feedback text and the feedback
            construction.create_edge(sc_types.EDGE_D_COMMON_CONST, 'feedback', text_link, 'text')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM, ScKeynodes.resolve('nrel_feedback_text', sc_types.NODE_CONST_NOROLE), 'text')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM,  ScKeynodes.resolve('concept_feedback_text', sc_types.NODE_CONST_CLASS), user_id_link)
            
            #creating relations between the required concepts and the feedback
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM,  ScKeynodes.resolve('concept_feedback', sc_types.NODE_CONST_CLASS), 'feedback')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM,  ScKeynodes.resolve('concept_feedback_not_considered', sc_types.NODE_CONST_CLASS), 'feedback')
            construction.create_edge(sc_types.EDGE_ACCESS_CONST_POS_PERM,  concept_report_type, 'feedback')
            
            addrs = create_elements(construction)

            if len(addrs) != 10:
                raise
            
            return ScResult.OK
        except Exception as e:
            self.logger.info(f"AgentReceiveFeedback: finished with an error {e}")
            return ScResult.ERROR