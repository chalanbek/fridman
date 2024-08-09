#include "MessageSearcher.hpp"

#include "sc-agents-common/keynodes/coreKeynodes.hpp"
#include "sc-agents-common/utils/IteratorUtils.hpp"

#include "keynodes/MessageKeynodes.hpp"
#include <algorithm>

using namespace scAgentsCommon;
using namespace dialogControlModule;

MessageSearcher::MessageSearcher(ScMemoryContext * ms_context)
{
  this->context = ms_context;
}

ScAddr MessageSearcher::getFirstMessage(const ScAddr & nonAtomicMessageNode)
{
  const std::string VAR_TUPLE = "_tuple";
  const std::string VAR_MESSAGE = "_message";
  ScTemplate templ;
  templ.TripleWithRelation(
      ScType::NodeVarTuple >> VAR_TUPLE,
      ScType::EdgeDCommonVar,
      nonAtomicMessageNode,
      ScType::EdgeAccessVarPosPerm,
      MessageKeynodes::nrel_message_decomposition);
  templ.TripleWithRelation(
      VAR_TUPLE,
      ScType::EdgeAccessVarPosPerm,
      ScType::NodeVar >> VAR_MESSAGE,
      ScType::EdgeAccessVarPosPerm,
      CoreKeynodes::rrel_1);

  ScTemplateSearchResult result;
  context->HelperSearchTemplate(templ, result);

  ScAddr resultMessageNode;
  if (result.Size() == 1)
  {
    resultMessageNode = result[0][VAR_MESSAGE];
    SC_LOG_DEBUG("MessageSearcher: the first message node found");
  }
  else
  {
    SC_LOG_DEBUG("MessageSearcher: the first message node not found");
  }

  return resultMessageNode;
}

ScAddr MessageSearcher::getNextMessage(const ScAddr & messageNode)
{
  const std::string VAR_TUPLE = "_tuple", VAR_EDGE_1 = "_edge_1", VAR_EDGE_2 = "_edge_2",
                    VAR_D_COMMON_EDGE = "_d_common_edge", VAR_MESSAGE = "_message";
  ScTemplate templ;
  templ.Triple(ScType::NodeVarTuple >> VAR_TUPLE, ScType::EdgeAccessVarPosPerm >> VAR_EDGE_1, messageNode);
  templ.TripleWithRelation(
      VAR_EDGE_1,
      ScType::EdgeDCommonVar >> VAR_D_COMMON_EDGE,
      ScType::EdgeAccessVarPosPerm >> VAR_EDGE_2,
      ScType::EdgeAccessVarPosPerm,
      MessageKeynodes::nrel_message_sequence);
  templ.Triple(VAR_TUPLE, VAR_EDGE_2, ScType::NodeVar >> VAR_MESSAGE);

  ScTemplateSearchResult result;
  context->HelperSearchTemplate(templ, result);

  ScAddr resultMessageNode;
  if (result.Size() > 0)
  {
    resultMessageNode = result[0][VAR_MESSAGE];
    SC_LOG_DEBUG("MessageSearcher: next message node found");
  }
  else
  {
    SC_LOG_DEBUG("MessageSearcher: next message node not found");
  }

  return resultMessageNode;
}

ScAddr MessageSearcher::getMessageAuthor(const ScAddr & messageNode)
{
  ScTemplate templ;
  const std::string VAR_AUTHOR = "_author";
  templ.TripleWithRelation(
      messageNode,
      ScType::EdgeDCommonVar,
      ScType::NodeVar >> VAR_AUTHOR,
      ScType::EdgeAccessVarPosPerm,
      MessageKeynodes::nrel_authors);

  ScTemplateSearchResult result;
  context->HelperSearchTemplate(templ, result);

  ScAddr resultAuthorNode;
  if (result.Size() > 0)
  {
    resultAuthorNode = result[0][VAR_AUTHOR];
    SC_LOG_DEBUG("MessageSearcher: author set node found");
  }
  else
  {
    SC_LOG_DEBUG("MessageSearcher: author set node not found");
  }

  return resultAuthorNode;
}

ScAddr MessageSearcher::getMessageTheme(const ScAddr & messageNode)
{
  ScTemplate templ;
  const std::string VAR_THEME = "_theme";
  templ.TripleWithRelation(
      messageNode,
      ScType::EdgeAccessVarPosPerm,
      ScType::NodeVar >> VAR_THEME,
      ScType::EdgeAccessVarPosPerm,
      MessageKeynodes::rrel_message_theme);

  ScTemplateSearchResult result;
  context->HelperSearchTemplate(templ, result);

  ScAddr resultThemeNode;
  if (result.Size() > 0)
  {
    resultThemeNode = result[0][VAR_THEME];
    SC_LOG_DEBUG("MessageSearcher: message theme node found");
  }
  else
  {
    SC_LOG_DEBUG("MessageSearcher: message theme node not found");
  }

  return resultThemeNode;
}

ScAddrVector MessageSearcher::getMessageLinks(ScAddr const & message, ScAddrVector const & linkClasses)
{
  ScAddrVector messageLinks;
  ScAddr const translationNode =
      utils::IteratorUtils::getAnyByInRelation(context, message, CoreKeynodes::nrel_sc_text_translation);
  if (!translationNode.IsValid())
  {
    SC_LOG_WARNING("MessageSearcher: text translation node not found");
    return {};
  }

  ScIterator3Ptr const linkIterator =
      context->Iterator3(translationNode, ScType::EdgeAccessConstPosPerm, ScType::LinkConst);
  while (linkIterator->Next())
  {
    ScAddr const & linkAddr = linkIterator->Get(2);
    bool result = std::all_of(linkClasses.cbegin(), linkClasses.cend(), [this, &linkAddr](auto const & addr) {
      return context->HelperCheckEdge(addr, linkAddr, ScType::EdgeAccessConstPosPerm);
    });

    if (result == SC_TRUE)
    {
      messageLinks.push_back(linkAddr);
    }
  }
  return messageLinks;
}

ScAddr MessageSearcher::getMessageLink(ScAddr const & message, ScAddrVector const & linkClasses)
{
  ScAddr messageLink;
  ScAddrVector messageLinks = getMessageLinks(message, linkClasses);
  if (!messageLinks.empty())
    messageLink = messageLinks.at(0);
  return messageLink;
}
