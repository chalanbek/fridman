#include "ScTemplateUtils.hpp"

ScAddrVector ScTemplateUtils::getAllWithKey(
    ScMemoryContext * context,
    const ScTemplate & scTemplate,
    const std::string & key)
{
  ScAddrVector elements;

  ScTemplateSearchResult templateResult;
  context->HelperSearchTemplate(scTemplate, templateResult);

  for (size_t i = 0; i < templateResult.Size(); i++)
  {
    elements.push_back(templateResult[i][key]);
  }

  return elements;
}
