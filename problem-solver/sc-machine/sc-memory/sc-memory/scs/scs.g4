grammar scs;

options
{
  language = Cpp;
}

tokens
{
}

@parser::header
{
#include "scsLexer.h"
#include "sc-memory/scs/scs_parser.hpp"

#include "sc-memory/sc_debug.hpp"

#define APPEND_ATTRS(__attrs, __edge) \
for (auto const & _a : __attrs) \
{ \
  ElementHandle const attrEdge = m_parser->ProcessConnector(_a.second ? "->" : "_->"); \
  m_parser->ProcessTriple(_a.first, attrEdge, __edge); \
}

#define PARSE_ERROR(line, pos, msg) \
  SC_THROW_EXCEPTION(utils::ExceptionParseError, \
                    "line " << line << ", " << pos << " " << msg);

}

@parser::members {

public:
  void setParser(scs::Parser * parser)
  {
    m_parser = parser;
  }

private:
  scs::Parser * m_parser;

public:

}

content returns [ElementHandle handle]
  locals [ bool isVar = false;]
  @init{ $ctx->isVar = false; }
  : ('_' { $ctx->isVar = true; } )?
      c=CONTENT_BODY
    {
      std::string v = $ctx->c->getText();
      $ctx->handle = m_parser->ProcessContent(v, $ctx->isVar);
    }
  ;

contour[ElementHandle contourHandle = ElementHandle()]
  returns [ElementHandle handle]
  : CONTOUR_BEGIN
    {
      $ctx->handle = $contourHandle.IsValid() ? $contourHandle : m_parser->ProcessEmptyContour();
      m_parser->ProcessContourBegin();
    }
    ( (sentence_wrap
	| (sentence_lvl_4_list_item[$ctx->handle] ';;'))* )
    CONTOUR_END
    {
      m_parser->ProcessContourEnd($ctx->handle);
    }
  ;

connector returns [std::string text]
  : c=('<>' | '>' | '<' | '..>' | '<..'
    | '->' | '<-' | '<=>' | '=>' | '<='
    | '-|>' | '<|-' | '-/>' | '</-'
    | '~>' | '<~' | '~|>' | '<|~'
    | '~/>' | '</~' | '_<>' | '_>' | '_<'
    | '_..>' | '_<..' | '<.._' | '_->' | '_<-'| '<-_'
    | '_<=>' | '_=>' | '_<=' |'<=_' | '_-|>' | '_<|-' | '<|-_'
    | '_-/>' | '_</-' | '</-_' | '_~>' | '_<~' | '<~_'
    | '_~|>' | '_<|~' | '<|~_' | '_~/>' | '_</~' | '</~_')

    {
      $ctx->text = $c->getText();
    }
  ;


// ------------- Rules --------------------

syntax 
  : sentence_wrap* EOF
  ;

sentence_wrap
  : (sentence ';;')
  ;

sentence
  : sentence_lvl1
  | sentence_assign
  | sentence_assign_contour
  | sentence_lvl_common
  ;

idtf_alias returns [ElementHandle handle]
  : ALIAS_SYMBOLS
    {
      std::string const _alias = $ALIAS_SYMBOLS->getText();
      $ctx->handle = m_parser->ResolveAlias(_alias);
      if (!$ctx->handle.IsValid())
      {
        PARSE_ERROR($ctx->start->getLine(), $ctx->start->getCharPositionInLine(),
          "Can't resolve alias `" << _alias << "`. You should assign an alias before use.");
      }
    }
  ;

idtf_system returns [ElementHandle handle]
  : ID_SYSTEM
    { $ctx->handle = m_parser->ProcessIdentifier($ID_SYSTEM->getText()); }
  | '...'
    { $ctx->handle = m_parser->ProcessIdentifier("..."); }
  | type=idtf_lvl1_preffix
    { $ctx->handle = m_parser->ProcessIdentifier($ctx->type->text); }
  ;


sentence_assign
  : ALIAS_SYMBOLS '=' i=idtf_common
    {
      m_parser->ProcessAssign($ALIAS_SYMBOLS->getText(), $ctx->i->handle);
    }
  ;

sentence_assign_contour
  : a=idtf_system '=' contour[$ctx->a->handle]
  ;
    
idtf_lvl1_preffix returns [std::string text]
  : type=('sc_node'
  | 'sc_link'
  | 'sc_edge_dcommon'
  | 'sc_edge_ucommon'
  | 'sc_edge_main'
  | 'sc_edge_access'
  
  // backward compatibility
  | 'sc_arc_common'
  | 'sc_edge'
  | 'sc_arc_main'
  | 'sc_arc_access')

  {
    $ctx->text = $ctx->type->getText();
  }
  ;
    
idtf_lvl1_value returns [ElementHandle handle]
   : type=idtf_lvl1_preffix '#' i=ID_SYSTEM
    {
      $ctx->handle = m_parser->ProcessIdentifierLevel1($ctx->type->text, $ctx->i->getText());
    }
  ;
    
idtf_lvl1 returns [ElementHandle handle]
  : idtf_lvl1_value { $ctx->handle = $idtf_lvl1_value.handle; }
  // | LINK
  ;

idtf_edge returns [ElementHandle handle]
  : '(' src=idtf_atomic
        c=connector attrs=attr_list?
        trg=idtf_atomic
    ')'

    {
      ElementHandle const edge = m_parser->ProcessConnector($ctx->c->text);
      m_parser->ProcessTriple($ctx->src->handle, edge, $ctx->trg->handle);

      // append attributes
      if ($ctx->attrs != nullptr)
      {
        APPEND_ATTRS($attrs.items, edge);
      }

      $ctx->handle = edge;
    }
  ;
  
idtf_set returns [ElementHandle handle]
  : '{' ctx_s=idtf_set_elements["set"] { $ctx->handle = $ctx->ctx_s->handle; } '}'
  | '<' ctx_v=idtf_set_elements["vector"] { $ctx->handle = $ctx->ctx_v->handle; } '>'
  ;

idtf_set_elements [std::string setType]
  returns [ElementHandle handle]
  locals [ElementHandle prevEdge]
  : {
      std::string const setIdtf = "..set_" + std::to_string($ctx->start->getLine()) + "_" + std::to_string($ctx->start->getCharPositionInLine());
      $ctx->handle = m_parser->ProcessIdentifier(setIdtf);
      ElementHandle const typeEdge = m_parser->ProcessConnector("->");
      ElementHandle const typeClass = m_parser->ProcessIdentifier("sc_node_tuple");

      m_parser->ProcessTriple(typeClass, typeEdge, $ctx->handle);
    }
  a1=attr_list? i1=idtf_common
    {
      ElementHandle const edge = m_parser->ProcessConnector("->");
      m_parser->ProcessTriple($ctx->handle, edge, $ctx->i1->handle);

      if ($ctx->a1 != nullptr)
      {
        APPEND_ATTRS($ctx->a1->items, edge);
      }

      if ($ctx->setType == "vector")
      {
        ElementHandle const relEdge = m_parser->ProcessConnector("->");
        ElementHandle const rel = m_parser->ProcessIdentifier("rrel_1");
        m_parser->ProcessTriple(rel, relEdge, edge);

        $ctx->prevEdge = edge;
      }
    }
    internal_sentence_list[$ctx->i1->handle]?

    (';'
    a2=attr_list? i2=idtf_common
      {
        ElementHandle const edge = m_parser->ProcessConnector("->");
        m_parser->ProcessTriple($ctx->handle, edge, $ctx->i2->handle);

        if ($ctx->a2 != nullptr)
        {
          APPEND_ATTRS($ctx->a2->items, edge);
        }

        if ($ctx->setType == "vector")
        {
          ElementHandle const seqEdge = m_parser->ProcessConnector("=>");
          m_parser->ProcessTriple($ctx->prevEdge, seqEdge, edge);

          ElementHandle const relEdge = m_parser->ProcessConnector("->");
          ElementHandle const rel = m_parser->ProcessIdentifier("nrel_basic_sequence");
          m_parser->ProcessTriple(rel, relEdge, seqEdge);

          $ctx->prevEdge = edge;
        }
      }
      internal_sentence_list[$ctx->i2->handle]?
    )*
  ;

idtf_atomic returns [ElementHandle handle]
  : a=idtf_alias { $ctx->handle = $ctx->a->handle; }
  | is=idtf_system { $ctx->handle = $ctx->is->handle; }
  ;

idtf_url returns [ElementHandle handle]
  : LINK
    {
      std::string const value = $LINK->getText();
      $ctx->handle = m_parser->ProcessFileURL(value.substr(1, value.size() - 2));
    }
  ;

idtf_common returns [ElementHandle handle]
  : a=idtf_atomic { $ctx->handle = $ctx->a->handle; }
  | ie=idtf_edge { $ctx->handle = $ctx->ie->handle; }
  | iset=idtf_set { $ctx->handle = $ctx->iset->handle; }
  | ct=contour[] { $ctx->handle = $ctx->ct->handle; }
  | cn=content { $ctx->handle = $ctx->cn->handle; }
  | u=idtf_url { $ctx->handle = $ctx->u->handle; }
  ;

idtf_list returns [std::vector<ElementHandle> items]
  : i1=idtf_common { $ctx->items.push_back($ctx->i1->handle); }
    internal_sentence_list[$ctx->i1->handle]? 
    (';' 
      i2=idtf_common { $items.push_back($ctx->i2->handle); }
      internal_sentence_list[$ctx->i2->handle]?
    )*
  ;

internal_sentence [ElementHandle source]
  : c=connector attrs=attr_list? targets=idtf_list
    {
      for (auto const & trg : $ctx->targets->items)
      {
        ElementHandle const edge = m_parser->ProcessConnector($c.text);
        m_parser->ProcessTriple(source, edge, trg);
        
        if ($ctx->attrs != nullptr)
        {
          APPEND_ATTRS($ctx->attrs->items, edge);
        }
      }
    }
    | internal_sentence_list[source]
  ;

internal_sentence_list [ElementHandle source]
  : '(*' (internal_sentence[source] ';;')+ '*)'
  ;

sentence_lvl1
   : src=idtf_lvl1 '|' edge=idtf_lvl1 '|' trg=idtf_lvl1
    {
      m_parser->ProcessTriple($ctx->src->handle, $ctx->edge->handle, $ctx->trg->handle);
    }
  ;

sentence_lvl_4_list_item [ElementHandle source]
  : c=connector attrs=attr_list? targets=idtf_list
    { 
      for (auto const & t : $ctx->targets->items)
      {
          ElementHandle const edge = m_parser->ProcessConnector($c.text);
          m_parser->ProcessTriple($source, edge, t);
          
          if ($ctx->attrs != nullptr)
          {
            APPEND_ATTRS($ctx->attrs->items, edge);
          }
      }
    }
  ;

sentence_lvl_common
  : src=idtf_common sentence_lvl_4_list_item[$ctx->src->handle]
    (';' sentence_lvl_4_list_item[$ctx->src->handle])*
  ;

attr_list returns [std::vector<std::pair<ElementHandle, bool>> items]
  @init { $items = {}; }
  : (
      ID_SYSTEM
      EDGE_ATTR
      {
        $ctx->items.emplace_back(m_parser->ProcessIdentifier($ID_SYSTEM->getText()),
                                 scs::TypeResolver::IsEdgeAttrConst($EDGE_ATTR->getText()));
      }
    )+
  ;


// ----------------------------
ID_SYSTEM
  : ('a'..'z'|'A'..'Z'|'_'|'.'|'0'..'9')+
  ;

ALIAS_SYMBOLS
  : '@'('a'..'z'|'A'..'Z'|'_'|'0'..'9')+
  ;

fragment CONTENT_ESCAPED
  : '\\' ('[' | ']' | '\\')
  ;

fragment CONTENT_SYBMOL
  : (CONTENT_ESCAPED | ~('[' | ']' | '\\'))
  ;

fragment CONTENT_SYBMOL_FIRST_END
  : (CONTENT_ESCAPED | ~('[' | ']' | '\\' | '*'))
  ;

CONTOUR_BEGIN
  : '[*'
  ;

CONTOUR_END
  : '*]'
  ;

CONTENT_BODY
  : '[]'
  | '![]!'
  | '[' CONTENT_SYBMOL_FIRST_END CONTENT_SYBMOL* ']'
  | '![' CONTENT_SYBMOL_FIRST_END CONTENT_SYBMOL* ']!'
  ;

LINK
  : '"' (~('"') | '\\"' )* '"'
  ;
  
EDGE_ATTR
  : ':'
  | '::';

LINE_TERMINATOR
  : [\r\n\u2028\u2029] -> channel(HIDDEN)
  ;
  
LINE_COMMENT
  : '//' ~('\n'|'\r')* '\r'? '\n' -> channel(HIDDEN)
  ;

MULTINE_COMMENT
  : '/*' .*? '*/' -> channel(HIDDEN)
  ;

WS :
  ( ' '
  | '\t'
  | '\r'
  | '\n'
  ) -> channel(HIDDEN)
  ;
