/*
 * This source file is part of an OSTIS project. For the latest info, see http://ostis.net
 * Distributed under the MIT License
 * (See accompanying file COPYING.MIT or copy at http://opensource.org/licenses/MIT)
 */

#pragma once

extern "C"
{
#include "sc-core/sc_memory_headers.h"
#include "sc-core/sc_helper.h"
}

#include "sc_addr.hpp"
#include "sc_event.hpp"
#include "sc_iterator.hpp"
#include "sc_stream.hpp"
#include "sc_template.hpp"
#include "sc_type.hpp"

class ScMemoryContext;

typedef struct _ScSystemIdentifierFiver
{
  ScAddr addr1;
  ScAddr addr2;
  ScAddr addr3;
  ScAddr addr4;
  ScAddr addr5;
} ScSystemIdentifierFiver;

class ScMemory
{
  friend class ScMemoryContext;

public:
  //! Returns true, on memory initialized; otherwise returns false
  _SC_EXTERN static bool Initialize(sc_memory_params const & params);
  _SC_EXTERN static bool IsInitialized();
  _SC_EXTERN static void Shutdown(bool saveState = true);

  _SC_EXTERN static void LogMute();
  _SC_EXTERN static void LogUnmute();

protected:
  static void RegisterContext(ScMemoryContext const * ctx);
  static void UnregisterContext(ScMemoryContext const * ctx);

private:
  static bool HasMemoryContext(ScMemoryContext const * ctx);

private:
  static sc_memory_context * ms_globalContext;

  using MemoryContextList = std::list<ScMemoryContext const *>;
  static MemoryContextList ms_contexts;
};

//! Class used to work with memory. It provides functions to create/erase elements
class ScMemoryContext
{
public:
  struct ScMemoryStatistics
  {
    sc_uint64 m_nodesNum;
    sc_uint64 m_linksNum;
    sc_uint64 m_edgesNum;

    sc_uint64 GetAllNum() const
    {
      return m_nodesNum + m_linksNum + m_edgesNum;
    }
  };

  using Stat = ScMemoryStatistics;

public:
  _SC_EXTERN explicit ScMemoryContext(sc_uint8 accessLevels, std::string const & name = "");
  _SC_EXTERN explicit ScMemoryContext(std::string const & name);
  _SC_EXTERN ~ScMemoryContext();

  // Disable object copying
  ScMemoryContext(ScMemoryContext const & other) = delete;
  ScMemoryContext & operator=(ScMemoryContext const & other) = delete;

  sc_memory_context const * operator*() const
  {
    return m_context;
  }
  sc_memory_context const * GetRealContext() const
  {
    return m_context;
  }

  //! Call this function, when you request to destroy real memory context, before destructor calls for this object
  _SC_EXTERN void Destroy();

  //! Begin events pending mode
  void BeingEventsPending();

  //! End events pending mode
  void EndEventsPending();

  // returns copy, because of Python wrapper
  std::string const & GetName() const
  {
    return m_name;
  }

  _SC_EXTERN bool IsValid() const;

  //! Check if element exists with specified addr
  _SC_EXTERN bool IsElement(ScAddr const & addr) const;

  //! Returns count of element output arcs
  _SC_EXTERN size_t GetElementOutputArcsCount(ScAddr const & addr) const;
  //! Returns count of element input arcs
  _SC_EXTERN size_t GetElementInputArcsCount(ScAddr const & addr) const;

  //! Erase element from sc-memory and returns true on success; otherwise returns false.
  _SC_EXTERN bool EraseElement(ScAddr const & addr);

  _SC_EXTERN ScAddr CreateNode(ScType const & type);
  _SC_EXTERN ScAddr CreateLink(ScType const & type = ScType::LinkConst);

  _SC_EXTERN ScAddr CreateEdge(ScType const & type, ScAddr const & addrBeg, ScAddr const & addrEnd);

  //! Returns type of sc-element. If there are any error, then returns ScType::Unknown
  _SC_EXTERN ScType GetElementType(ScAddr const & addr) const;

  /*! Change subtype of sc-element.
   * Return true, if there are no any errors; otherwise return false.
   */
  _SC_EXTERN bool SetElementSubtype(ScAddr const & addr, sc_type subtype);

  _SC_EXTERN ScAddr GetEdgeSource(ScAddr const & edgeAddr) const;
  _SC_EXTERN ScAddr GetEdgeTarget(ScAddr const & edgeAddr) const;
  _SC_EXTERN bool GetEdgeInfo(ScAddr const & edgeAddr, ScAddr & outSourceAddr, ScAddr & outTargetAddr) const;

  _SC_EXTERN bool SetLinkContent(ScAddr const & addr, ScStreamPtr const & stream, bool isSearchableString = true);
  template <typename TContentType>
  bool SetLinkContent(ScAddr const & addr, TContentType const & value, bool isSearchableString = true)
  {
    return SetLinkContent(addr, ScStreamMakeRead(value), isSearchableString);
  }

  _SC_EXTERN bool GetLinkContent(ScAddr const & addr, std::string & typedContent)
  {
    ScStreamPtr const & ptr = GetLinkContent(addr);
    return ptr != nullptr && ptr->IsValid() && ScStreamConverter::StreamToString(ptr, typedContent);
  }

  _SC_EXTERN ScStreamPtr GetLinkContent(ScAddr const & addr);
  template <typename TContentType>
  bool GetLinkContent(ScAddr const & addr, TContentType & typedContent)
  {
    std::string content;
    ScStreamPtr const & ptr = GetLinkContent(addr);
    if (ptr != nullptr && ptr->IsValid() && ScStreamConverter::StreamToString(ptr, content))
    {
      std::istringstream streamString{content};
      streamString >> typedContent;

      return SC_TRUE;
    }

    return SC_FALSE;
  }

  _SC_EXTERN ScAddrVector FindLinksByContent(ScStreamPtr const & stream);
  template <typename TContentType>
  ScAddrVector FindLinksByContent(TContentType const & value)
  {
    return FindLinksByContent(ScStreamMakeRead(value));
  }

  template <typename TContentType>
  ScAddrVector FindLinksByContentSubstring(TContentType const & value, size_t maxLengthToSearchAsPrefix = 0)
  {
    return FindLinksByContentSubstring(ScStreamMakeRead(value), maxLengthToSearchAsPrefix);
  }
  _SC_EXTERN ScAddrVector FindLinksByContentSubstring(ScStreamPtr const & stream, size_t maxLengthToSearchAsPrefix = 0);

  template <typename TContentType>
  std::vector<std::string> FindLinksContentsByContentSubstring(
      TContentType const & value,
      size_t maxLengthToSearchAsPrefix = 0)
  {
    return FindLinksContentsByContentSubstring(ScStreamMakeRead(value), maxLengthToSearchAsPrefix);
  }
  _SC_EXTERN std::vector<std::string> FindLinksContentsByContentSubstring(
      ScStreamPtr const & stream,
      size_t maxLengthToSearchAsPrefix = 0);

  //! Saves memory state
  _SC_EXTERN bool Save();

  template <typename ParamType1, typename ParamType2, typename ParamType3, typename ParamType4, typename ParamType5>
  std::shared_ptr<TIterator5<ParamType1, ParamType2, ParamType3, ParamType4, ParamType5>> Iterator5(
      ParamType1 const & param1,
      ParamType2 const & param2,
      ParamType3 const & param3,
      ParamType4 const & param4,
      ParamType5 const & param5)
  {
    return std::shared_ptr<TIterator5<ParamType1, ParamType2, ParamType3, ParamType4, ParamType5>>(
        new TIterator5<ParamType1, ParamType2, ParamType3, ParamType4, ParamType5>(
            *this, param1, param2, param3, param4, param5));
  }

  template <typename ParamType1, typename ParamType2, typename ParamType3>
  std::shared_ptr<TIterator3<ParamType1, ParamType2, ParamType3>> Iterator3(
      ParamType1 const & param1,
      ParamType2 const & param2,
      ParamType3 const & param3)
  {
    return std::shared_ptr<TIterator3<ParamType1, ParamType2, ParamType3>>(
        new TIterator3<ParamType1, ParamType2, ParamType3>(*this, param1, param2, param3));
  }

  /* Make iteration by triples, and call fn function for each result.
   * fn function should have 3 parameters (ScAddr const & source, ScAddr const & edge, ScAddr const & target)
   */
  template <typename ParamType1, typename ParamType2, typename ParamType3, typename FnT>
  void ForEachIter3(ParamType1 const & param1, ParamType2 const & param2, ParamType3 const & param3, FnT && fn)
  {
    ScIterator3Ptr it = Iterator3(param1, param2, param3);
    while (it->Next())
      fn(it->Get(0), it->Get(1), it->Get(2));
  }

  /* Make iteration by 5-element constructions, and call fn function for each result.
   * fn function should have 5 parameters
   * (ScAddr const & source, ScAddr const & edge, ScAddr const & target, ScAddr const & attrEdge, ScAddr const & attr)
   */
  template <
      typename ParamType1,
      typename ParamType2,
      typename ParamType3,
      typename ParamType4,
      typename ParamType5,
      typename FnT>
  void ForEachIter5(
      ParamType1 const & param1,
      ParamType2 const & param2,
      ParamType3 const & param3,
      ParamType4 const & param4,
      ParamType5 const & param5,
      FnT && fn)
  {
    ScIterator5Ptr it = Iterator5(param1, param2, param3, param4, param5);
    while (it->Next())
      fn(it->Get(0), it->Get(1), it->Get(2), it->Get(3), it->Get(4));
  }

  /*! Tries to resolve ScAddr by it system identifier. If element with specified identifier doesn't exist
   * and type is not empty, then it would be created with specified type.
   * Important: Type should be any of ScType::Node...
   * @param sysIdtf System identifier of resolving sc-element address
   * @param type Sc-type of resolving sc-element address
   * @returns ScAddr of resolved sc-element address.
   * @throws utils::ExceptionInvalidParams if resolving sc-element type is not ScType::Node subtype.
   */
  _SC_EXTERN ScAddr HelperResolveSystemIdtf(std::string const & sysIdtf, ScType const & type = ScType());

  /*! Tries to resolve ScAddr by it system identifier. If element with specified identifier doesn't exist
   * and type is not empty, then it would be created with specified type.
   * Important: Type should be any of ScType::Node...
   * @param sysIdtf System identifier of resolving sc-element address
   * @param type Sc-type of resolving sc-element address
   * @param outFiver[out] The 1st, 2d, 3d, 4th, 5th sc-element addresses of system identifier fiver of resolved
   * sc-element address with `sysIdtf`
   *                              addr1 (resolved sc-element address)
   *                addr4           |
   *        addr5 --------------->  | addr2
   *     (nrel_system_identifier)   |
   *                              addr3 (system identifier sc-link)
   * @returns true if sc-element address resolved.
   * @throws utils::ExceptionInvalidParams if resolving sc-element type is not ScType::Node subtype.
   */
  _SC_EXTERN bool HelperResolveSystemIdtf(
      std::string const & sysIdtf,
      ScType const & type,
      ScSystemIdentifierFiver & outFiver);

  /*! Tries to set system identifier for sc-element ScAddr.
   * @param sysIdtf System identifier to set for sc-element `addr`
   * @param addr Sc-element address to set `sysIdtf` for it
   * @returns false if `sysIdtf` set for other sc-element address.
   */
  _SC_EXTERN bool HelperSetSystemIdtf(std::string const & sysIdtf, ScAddr const & addr);

  /*! Tries to set system identifier for sc-element ScAddr.
   * @param sysIdtf System identifier to set for sc-element `addr`
   * @param addr Sc-element address to set `sysIdtf` for it
   * @param outFiver[out] The 1st, 2d, 3d, 4th, 5th sc-element addresses of system identifier fiver of sc-element `addr`
   * with set `sysIdtf`
   *                              addr1 (`addr`)
   *                addr4           |
   *        addr5 --------------->  | addr2
   *     (nrel_system_identifier)   |
   *                              addr3 (system identifier sc-link)
   * @returns false if `sysIdtf` set for other sc-element address.
   */
  _SC_EXTERN bool HelperSetSystemIdtf(
      std::string const & sysIdtf,
      ScAddr const & addr,
      ScSystemIdentifierFiver & resultFiver);

  /*! Tries to get system identifier for sc-element ScAddr.
   * @param addr Sc-element address to get it system identifier
   * @returns "" if system identifier doesn't exist for `addr`.
   */
  _SC_EXTERN std::string HelperGetSystemIdtf(ScAddr const & addr);

  _SC_EXTERN bool HelperCheckEdge(ScAddr const & begin, ScAddr end, ScType const & edgeType);

  _SC_EXTERN bool HelperFindBySystemIdtf(std::string const & sysIdtf, ScAddr & outAddr);
  _SC_EXTERN ScAddr HelperFindBySystemIdtf(std::string const & sysIdtf);
  _SC_EXTERN bool HelperFindBySystemIdtf(std::string const & sysIdtf, ScSystemIdentifierFiver & outFiver);

  _SC_EXTERN ScTemplate::Result HelperGenTemplate(
      ScTemplate const & templ,
      ScTemplateGenResult & result,
      ScTemplateParams const & params = ScTemplateParams::Empty,
      ScTemplateResultCode * resultCode = nullptr) noexcept(false);
  SC_DEPRECATED(
      0.8.0,
      "Use callback-based ScMemoryContext::HelperSearchTemplate(ScTemplate const & templ, "
      "ScTemplateSearchResultCallback const & callback, ScTemplateSearchResultCheckCallback const & checkCallback) "
      "instead.")
  _SC_EXTERN ScTemplate::Result HelperSearchTemplate(
      ScTemplate const & templ,
      ScTemplateSearchResult & result) noexcept(false);

  /*!
   * Searches sc-constructions by isomorphic search template and pass search result construction to `callback`
   * lambda-function. If `filterCallback` passed, then all found constructions triples are filtered by `filterCallback`
   * condition.
   * @param templ A sc-template object to find constructions by it
   * @param callback A lambda-function, callable when each construction triple was found
   * @param filterCallback A lambda-function, that filters all found constructions triples
   * @param checkCallback A lambda-function, that filters all found triples with checking sc-address
   * @example
   * \code
   * ...
   * ...
   * ScAddr const & structureAddr = ctx.CreateNode(ScType::NodeConstStruct);
   * ScAddr const & modelAddr = ctx.CreateNode(ScType::NodeConstStruct);
   * ...
   * ScAddr const & setAddr = ctx.CreateNode(ScType::NodeConst);
   * ScTemplate templ;
   * templ.Triple(
   *  classAddr,
   *  ScType::EdgeAccessVarPosPerm >> "_edge",
   *  ScType::Unknown >> "_addr2"
   * );
   * m_ctx->HelperSearchTemplate(templ, [&ctx](ScTemplateSearchResultItem const & item) {
   *  ctx.CreateEdge(ScType::EdgeAccessConstPosTemp, setAddr, item["_addr2"]);
   * }, [&ctx](ScTemplateSearchResultItem const & item) -> bool {
   *  return !ctx->HelperCheckEdge(structureAddr, item["_edge"], ScType::EdgeAccessConstPosPerm);
   * }, [&ctx](ScAddr const & addr) -> bool {
   *  return ctx->HelperCheckEdge(modelAddr, addr, ScType::EdgeAccessConstPosPerm);
   * });
   * \endcode
   * @throws utils::ExceptionInvalidState if sc-template is not valid
   */
  _SC_EXTERN void HelperSearchTemplate(
      ScTemplate const & templ,
      ScTemplateSearchResultCallback const & callback,
      ScTemplateSearchResultFilterCallback const & filterCallback = {},
      ScTemplateSearchResultCheckCallback const & checkCallback = {}) noexcept(false);

  _SC_EXTERN void HelperSearchTemplate(
      ScTemplate const & templ,
      ScTemplateSearchResultCallback const & callback,
      ScTemplateSearchResultCheckCallback const & checkCallback) noexcept(false);

  /*!
   * Searches constructions by isomorphic search template and pass search result construction to `callback`
   * lambda-function. Lambda-function `callback` must return a request command value to manage sc-template search:
   *  - ScTemplateSearchRequest::CONTINUE,
   *  - ScTemplateSearchRequest::STOP,
   *  - ScTemplateSearchRequest::ERROR.
   * When ScTemplateSearchRequest::CONTINUE returned sc-template search will be continued. If
   * ScTemplateSearchRequest::STOP or ScTemplateSearchRequest::ERROR, then sc-template search stops. If sc-template
   * search stopped by ScTemplateSearchRequest::ERROR, then HelperSmartSearchTemplate throws
   * utils::ExceptionInvalidState.
   * If `filterCallback` passed, then all found constructions triples are filtered by `filterCallback` condition.
   * @param templ A sc-template object to find constructions by it
   * @param callback A lambda-function, callable when each construction triple was found
   * @param filterCallback A lambda-function, that filters all found constructions triples
   * @param checkCallback A lambda-function, that filters all found triples with checking sc-address
   * @example
   * \code
   * ...
   * ...
   * ScAddr const & structureAddr = ctx.CreateNode(ScType::NodeConstStruct);
   * ...
   * ScAddr const & setAddr = ctx.CreateNode(ScType::NodeConst);
   * ScTemplate templ;
   * templ.Triple(
   *  classAddr,
   *  ScType::EdgeAccessVarPosPerm >> "_edge",
   *  ScType::Unknown >> "_addr2"
   * );
   * m_ctx->HelperSmartSearchTemplate(templ, [&ctx](ScTemplateSearchResultItem const & item) -> ScTemplateSearchRequest
   * {
   *   if (ctx->HelperCheckEdge(structureAddr, edgeAddr, ScType::EdgeAccessConstPosPerm))
   *    return ScTemplateSearchRequest::CONTINUE;
   *
   *   if (ctx.CreateEdge(ScType::EdgeAccessConstPosTemp, setAddr, item["_addr2"]))
   *    return ScTemplateSearchRequest::STOP;
   *
   *   return ScTemplateSearchRequest::ERROR;
   * });
   * \endcode
   * @throws utils::ExceptionInvalidState if sc-template is not valid
   */
  _SC_EXTERN void HelperSmartSearchTemplate(
      ScTemplate const & templ,
      ScTemplateSearchResultCallbackWithRequest const & callback,
      ScTemplateSearchResultFilterCallback const & filterCallback = {},
      ScTemplateSearchResultCheckCallback const & checkCallback = {}) noexcept(false);

  _SC_EXTERN void HelperSmartSearchTemplate(
      ScTemplate const & templ,
      ScTemplateSearchResultCallbackWithRequest const & callback,
      ScTemplateSearchResultCheckCallback const & checkCallback) noexcept(false);

  SC_DEPRECATED(
      0.8.0,
      "Use callback-based ScMemoryContext::HelperSearchTemplate(ScTemplate const & templ, "
      "ScTemplateSearchResultCallback const & callback, ScTemplateSearchResultCheckCallback const & checkCallback) "
      "instead.")
  _SC_EXTERN ScTemplate::Result HelperSearchTemplateInStruct(
      ScTemplate const & templ,
      ScAddr const & scStruct,
      ScTemplateSearchResult & result) noexcept(false);
  _SC_EXTERN ScTemplate::Result HelperBuildTemplate(
      ScTemplate & templ,
      ScAddr const & templAddr,
      const ScTemplateParams & params = ScTemplateParams()) noexcept(false);
  _SC_EXTERN ScTemplate::Result HelperBuildTemplate(ScTemplate & templ, std::string const & scsText) noexcept(false);

  _SC_EXTERN ScMemoryStatistics CalculateStat() const;

private:
  sc_memory_context * m_context;
  std::string m_name;
};

class ScMemoryContextEventsPendingGuard
{
public:
  _SC_EXTERN explicit ScMemoryContextEventsPendingGuard(ScMemoryContext & ctx)
    : m_ctx(ctx)
  {
    m_ctx.BeingEventsPending();
  }

  _SC_EXTERN ~ScMemoryContextEventsPendingGuard()
  {
    m_ctx.EndEventsPending();
  }

private:
  ScMemoryContext & m_ctx;
};
