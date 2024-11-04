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
            nrel_main_idtf = ScKeynodes.resolve('nrel_main_idtf', sc_types.NODE_CONST_NOROLE)
            lang_ru = ScKeynodes.resolve("lang_ru", sc_types.NODE_CONST_CLASS)
            topic_list = []

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
                    sc_types.EDGE_D_COMMON_VAR >> '_topic_this_arc',
                    sc_types.NODE_VAR >> '_topic',
                    sc_types.EDGE_ACCESS_VAR_POS_PERM,
                    nrel_subtopic
                )
                topics = template_search(template)
                for topic in topics:
                    topic_this = topic.get('_topic')
                    topic_this_arc = topic.get('_topic_this_arc')

                    template = ScTemplate()
                    template.triple_with_relation(
                        sc_types.EDGE_D_COMMON_VAR,
                        (sc_types.EDGE_D_COMMON_VAR, '_topic_squence_arc'),
                        topic_this_arc,
                        sc_types.EDGE_ACCESS_VAR_POS_PERM,
                        nrel_subtopic_sequence
                    )
                    if len(template_search(template)) == 0:
                        topic_sequence_current_arc = topic_this_arc
                        template = ScTemplate()
                        template.triple_with_relation(
                            topic_this,
                            sc_types.EDGE_D_COMMON_VAR,
                            sc_types.LINK_VAR >> 'link',
                            sc_types.EDGE_ACCESS_VAR_POS_PERM,
                            nrel_main_idtf
                        )
                        links = template_search(template)
                        for link in links:
                            template = ScTemplate()
                            template.triple(
                                lang_ru,
                                sc_types.EDGE_ACCESS_VAR_POS_PERM,
                                link.get('link') >> '_link'
                            )
                            result = template_search(template)
                            if len(result) == 1:
                                result = result[0].get('_link')
                                break

                        result = get_link_content_data(result)
                        topic_list.append(result)
                        break

                for topic in topics:
                    #topic_list.append(topic_sequence_current)
                    template = ScTemplate()
                    template.triple_with_relation(
                        topic_sequence_current_arc,
                        sc_types.EDGE_D_COMMON_VAR,
                        (sc_types.EDGE_D_COMMON_VAR, '_topic_next_arc'),
                        sc_types.EDGE_ACCESS_VAR_POS_PERM,
                        nrel_subtopic_sequence
                    )
                    result1 = template_search(template)
                    if len(result1) == 0:
                        break
                    topic_next_arc = result1[0].get('_topic_next_arc')
                    topic_sequence_current_arc = topic_next_arc
                    ## вроде так, но надо проверить
                    template = ScTemplate()
                    template.triple(
                        topic_addr,
                        topic_next_arc,
                        sc_types.NODE_VAR >> '_topic_next'
                    )
                    template.triple_with_relation(
                        '_topic_next',
                        sc_types.EDGE_D_COMMON_VAR,
                        sc_types.LINK_VAR >> 'link',
                        sc_types.EDGE_ACCESS_VAR_POS_PERM,
                        nrel_main_idtf
                    )
                    links = template_search(template)
                    for link in links:
                        template = ScTemplate()
                        template.triple(
                            lang_ru,
                            sc_types.EDGE_ACCESS_VAR_POS_PERM,
                            link.get('link') >> '_link'
                        )
                        result = template_search(template)
                        if len(result) == 1:
                            result = result[0].get('_link')
                            break

                    result = get_link_content_data(result)
                    topic_list.append(result)

                
                data = {1:topic_list}
                text = str(json.dumps(data))
                
                construction = ScConstruction()
                construction.create_link(sc_types.LINK_CONST, ScLinkContent(text, ScLinkContentType.STRING))
                addrs = create_elements(construction)
                link_answer = addrs[0]
                
                create_action_answer(action_node, link_answer)
                return ScResult.OK
            else:
                
                data = {1:[]}
                text = str(json.dumps(data))
                
                construction = ScConstruction()
                construction.create_link(sc_types.LINK_CONST, ScLinkContent(text, ScLinkContentType.STRING))
                addrs = create_elements(construction)
                link_answer = addrs[0]
                
                create_action_answer(action_node, link_answer)

                return ScResult.OK

        except Exception as e:
            self.logger.info(f"AgentGetCatalogProblems: finished with an error {e}")
            return ScResult.ERROR