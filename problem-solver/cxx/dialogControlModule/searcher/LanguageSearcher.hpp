#include "sc-memory/kpm/sc_agent.hpp"

namespace dialogControlModule
{
class LanguageSearcher
{
public:
  explicit LanguageSearcher(ScMemoryContext * ms_context);

  ScAddr getMessageLanguage(const ScAddr & messageNode);

  ScAddr getLanguage(const ScAddr & node);

private:
  ScMemoryContext * context;
};
}  // namespace dialogControlModule
