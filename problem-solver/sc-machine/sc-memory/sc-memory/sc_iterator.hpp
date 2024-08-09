/*
 * This source file is part of an OSTIS project. For the latest info, see http://ostis.net
 * Distributed under the MIT License
 * (See accompanying file COPYING.MIT or copy at http://opensource.org/licenses/MIT)
 */

#pragma once

#include "sc_addr.hpp"
#include "sc_utils.hpp"

extern "C"
{
#include "sc-core/sc_memory_headers.h"
}

class ScMemoryContext;

template <typename IterType, sc_uint8 tripleSize>
class TIteratorBase
{
public:
  virtual ~TIteratorBase() = default;

  inline bool IsValid() const
  {
    return m_iterator != nullptr;
  }

  //! Returns false, if there are no more iterator results. It more results exists, then go to next one and returns true
  _SC_EXTERN virtual bool Next() const = 0;

  //! Returns sc-addr of specified element in iterator result
  _SC_EXTERN virtual ScAddr Get(size_t index) const = 0;

  //! Returns sc-addr triple
  _SC_EXTERN virtual std::array<ScAddr, tripleSize> Get() const = 0;

  //! Short form of Get
  inline ScAddr operator[](size_t idx) const
  {
    return Get(idx);
  }

protected:
  IterType * m_iterator;
  size_t m_tripleSize = tripleSize;
};

using ScAddrTriple = std::array<ScAddr, 3>;
using ScAddrFiver = std::array<ScAddr, 5>;

template <typename ParamType1, typename ParamType2, typename ParamType3>
class TIterator3 : public TIteratorBase<sc_iterator3, 3>
{
  friend class ScMemoryContext;

protected:
  _SC_EXTERN TIterator3(
      ScMemoryContext const & context,
      ParamType1 const & p1,
      ParamType2 const & p2,
      ParamType3 const & p3);

public:
  _SC_EXTERN virtual ~TIterator3()
  {
    Destroy();
  }

  TIterator3(TIterator3 const & other)
  {
  }

  TIterator3 & operator=(TIterator3 const & other)
  {
    TakeOwnership(other);
    return *this;
  }

  void Destroy()
  {
    if (m_iterator)
    {
      sc_iterator3_free(m_iterator);
      m_iterator = nullptr;
    }
  }

  _SC_EXTERN bool Next() const override
  {
    SC_ASSERT(IsValid(), ("Not valid iterator object"));
    return sc_iterator3_next(m_iterator) == SC_TRUE;
  }

  _SC_EXTERN ScAddr Get(size_t index) const override
  {
    SC_ASSERT(IsValid(), ("Not valid iterator object"));
    if (index < m_tripleSize)
    {
      return ScAddr(sc_iterator3_value(m_iterator, index));
    }

    SC_THROW_EXCEPTION(
        utils::ExceptionInvalidParams,
        "Index=" + std::to_string(index) + " must be < size=" + std::to_string(m_tripleSize));
  }

  _SC_EXTERN ScAddrTriple Get() const override
  {
    SC_ASSERT(IsValid(), ("Not valid iterator object"));
    return {Get(0), Get(1), Get(2)};
  }
};

// ---------------------------
template <typename ParamType1, typename ParamType2, typename ParamType3, typename ParamType4, typename ParamType5>
class TIterator5 : public TIteratorBase<sc_iterator5, 5>
{
  friend class ScMemoryContext;

protected:
  _SC_EXTERN TIterator5(
      ScMemoryContext const & context,
      ParamType1 const & p1,
      ParamType2 const & p2,
      ParamType3 const & p3,
      ParamType4 const & p4,
      ParamType5 const & p5);

public:
  _SC_EXTERN ~TIterator5() override
  {
    Destroy();
  }

  void Destroy()
  {
    if (m_iterator)
    {
      sc_iterator5_free(m_iterator);
      m_iterator = 0;
    }
  }

  _SC_EXTERN bool Next() const override
  {
    SC_ASSERT(IsValid(), ("Not valid iterator object"));
    return sc_iterator5_next(m_iterator) == SC_TRUE;
  }

  _SC_EXTERN ScAddr Get(size_t index) const override
  {
    SC_ASSERT(IsValid(), ("Not valid iterator object"));
    if (index < m_tripleSize)
    {
      return sc_iterator5_value(m_iterator, index);
    }

    SC_THROW_EXCEPTION(
        utils::ExceptionInvalidParams,
        "Index=" + std::to_string(index) + " must be < size=" + std::to_string(m_tripleSize));
  }

  _SC_EXTERN ScAddrFiver Get() const override
  {
    SC_ASSERT(IsValid(), ("Not valid iterator object"));
    return {Get(0), Get(1), Get(2), Get(3), Get(4)};
  }
};

typedef TIteratorBase<sc_iterator3, 3> ScIterator3Type;
typedef TIteratorBase<sc_iterator5, 5> ScIterator5Type;

typedef std::shared_ptr<ScIterator3Type> ScIterator3Ptr;
typedef std::shared_ptr<ScIterator5Type> ScIterator5Ptr;
