# ==============================================================================
# Authors:            Patrick Lehmann
#
# Python functions:   A streaming VHDL parser
#
# Description:
# ------------------------------------
#		TODO:
#
# License:
# ==============================================================================
# Copyright 2017-2021 Patrick Lehmann - Boetzingen, Germany
# Copyright 2016-2017 Patrick Lehmann - Dresden, Germany
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
#
# load dependencies
from pydecor.decorators           import export

from pyVHDLParser.Token           import FusedCharacterToken, CharacterToken, WordToken, LiteralToken, SpaceToken, LinebreakToken
from pyVHDLParser.Token           import CommentToken, Token, MultiLineCommentToken, IndentationToken, SingleLineCommentToken
from pyVHDLParser.Token.Keywords  import EqualOperator, PlusOperator, MinusOperator, MultiplyOperator, DivideOperator, ConcatOperator, LessThanOperator
from pyVHDLParser.Token.Keywords  import GreaterThanOperator, DelimiterToken, PowerOperator, UnequalOperator, LessThanOrEqualOperator
from pyVHDLParser.Token.Keywords  import GreaterThanOrEqualOperator, MatchingEqualOperator, MatchingUnequalOperator, MatchingLessThanOperator
from pyVHDLParser.Token.Keywords  import MatchingLessThanOrEqualOperator, MatchingGreaterThanOperator, MatchingGreaterThanOrEqualOperator, OrKeyword
from pyVHDLParser.Token.Keywords  import NorKeyword, AndKeyword, NandKeyword, XorKeyword, XnorKeyword, SlaKeyword, SllKeyword, SraKeyword, SrlKeyword
from pyVHDLParser.Token.Keywords  import NotKeyword, AbsKeyword, OpeningRoundBracketToken, BoundaryToken, ClosingRoundBracketToken, IdentifierToken
from pyVHDLParser.Token.Keywords  import LoopKeyword, ToKeyword, DowntoKeyword, EndToken
from pyVHDLParser.Blocks          import Block, ParserState, BlockParserException, CommentBlock
from pyVHDLParser.Blocks.Common   import LinebreakBlock, WhitespaceBlock

__all__ = []
__api__ = __all__


@export
class ExpressionBlock(Block):
	CHARACTER_TRANSLATION = {
		"=":    EqualOperator,
		"+":    PlusOperator,
		"-":    MinusOperator,
		"*":    MultiplyOperator,
		"/":    DivideOperator,
		"&":    ConcatOperator,
		"<":    LessThanOperator,
		">":    GreaterThanOperator,
		",":    DelimiterToken
		# ";":    EndToken
	}
	FUSED_CHARACTER_TRANSLATION = {
		"**":   PowerOperator,
		"/=":   UnequalOperator,
		"<=":   LessThanOrEqualOperator,
		">=":   GreaterThanOrEqualOperator,
		"?=":   MatchingEqualOperator,
		"?/=":  MatchingUnequalOperator,
		"?<":   MatchingLessThanOperator,
		"?<=":  MatchingLessThanOrEqualOperator,
		"?>":   MatchingGreaterThanOperator,
		"?>=":  MatchingGreaterThanOrEqualOperator
		# "=>":   MapAssociationKeyword,
		# "<=>":  SignalAssociationKeyword
	}
	OPERATOR_TRANSLATIONS = {
		"or":    OrKeyword,
		"nor":   NorKeyword,
		"and":   AndKeyword,
		"nand":  NandKeyword,
		"xor":   XorKeyword,
		"xnor":  XnorKeyword,
		"sla":   SlaKeyword,
		"sll":   SllKeyword,
		"sra":   SraKeyword,
		"srl":   SrlKeyword,
		"not":   NotKeyword,
		"abs":   AbsKeyword
	}


@export
class ExpressionBlockEndedByCharORClosingRoundBracket(ExpressionBlock):
	EXIT_CHAR:  str =   None
	EXIT_TOKEN: Token = None
	EXIT_BLOCK: Block = None


	@classmethod
	def stateBeforeExpression(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, CharacterToken):
			if (token == "("):
				parserState.NewToken =    OpeningRoundBracketToken(token)
				parserState.Counter +=    1
				parserState.NextState =   cls.stateExpression
				return
			else:
				parserState.NewToken =    cls.CHARACTER_TRANSLATION[token.Value](token)
				parserState.NextState =   cls.stateExpression
				return
		elif isinstance(token, WordToken):
			try:
				parserState.NewToken =    cls.OPERATOR_TRANSLATIONS[token.Value](token)
			except KeyError:
				parserState.NewToken =    IdentifierToken(token)
			parserState.NextState =     cls.stateExpression
			return
		elif isinstance(token, LiteralToken):
			parserState.NextState =     cls.stateExpression
			return
		elif isinstance(token, LinebreakToken):
			parserState.NewBlock =      LinebreakBlock(parserState.LastBlock, token)
			parserState.TokenMarker =   None
			return
		elif isinstance(token, CommentToken):
			parserState.NewBlock =      CommentBlock(parserState.NewBlock, token)
			parserState.TokenMarker =   None
			return
		elif (isinstance(token, IndentationToken) and isinstance(token.PreviousToken, (LinebreakToken, SingleLineCommentToken))):
			return
		elif isinstance(token, SpaceToken):
			parserState.NextState =     cls.stateWhitespace1
			return

		raise BlockParserException("Expected '(', unary operator, identifier, literal or whitespace.", token)

	@classmethod
	def stateExpression(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, FusedCharacterToken):
			try:
				parserState.NewToken = cls.FUSED_CHARACTER_TRANSLATION[token.Value](token)
				return
			except KeyError:
				if (token == cls.EXIT_CHAR):
					if (parserState.Counter == 0):
						parserState.NewToken = cls.EXIT_TOKEN(token)
						parserState.NewBlock = cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
						_ =                    cls.EXIT_BLOCK(parserState.NewBlock, parserState.NewToken, endToken=parserState.NewToken)
						parserState.Pop(2)
						return
					else:
						raise BlockParserException("Mismatch in opening and closing parenthesis. Counter={0}".format(parserState.Counter), token)
		elif isinstance(token, CharacterToken):
			if (token == cls.EXIT_CHAR):
				if (parserState.Counter == 0):
					parserState.NewToken =  cls.EXIT_TOKEN(token)
					parserState.NewBlock =  cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
					_ =                     cls.EXIT_BLOCK(parserState.NewBlock, parserState.NewToken, endToken=parserState.NewToken)
					parserState.Pop(2)
					return
				else:
					raise BlockParserException("Mismatch in opening and closing parenthesis. Counter={0}".format(parserState.Counter), token)
			elif (token == "("):
				parserState.NewToken =    OpeningRoundBracketToken(token)
				parserState.Counter +=    1
				return
			elif (token == ")"):
				if (parserState.Counter == 0):
					parserState.NewToken =    BoundaryToken(token)
					parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
					parserState.Pop(3, parserState.NewToken)
					return
				else:
					parserState.NewToken =    ClosingRoundBracketToken(token)
					parserState.Counter -=    1
					return
			else:
				parserState.NewToken =    cls.CHARACTER_TRANSLATION[token.Value](token)
				return
		elif isinstance(token, WordToken):
			try:
				parserState.NewToken =    cls.OPERATOR_TRANSLATIONS[token.Value](token)
			except KeyError:
				parserState.NewToken =    IdentifierToken(token)
			return
		elif isinstance(token, LiteralToken):
			return
		elif isinstance(token, SpaceToken):
			parserState.NextState =     cls.stateWhitespace1
			return
		elif isinstance(token, (LinebreakToken, CommentToken)):
			block =                     LinebreakBlock if isinstance(token, LinebreakToken) else CommentBlock
			parserState.NewBlock =      cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
			_ =                         block(parserState.NewBlock, token)
			parserState.TokenMarker =   None
			parserState.NextState =     cls.stateWhitespace1
			return

		raise BlockParserException("Expected ?????????????.", token)

	@classmethod
	def stateWhitespace1(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, FusedCharacterToken):
			try:
				parserState.NewToken =    cls.FUSED_CHARACTER_TRANSLATION[token.Value](token)
				parserState.NextState =   cls.stateExpression
				return
			except KeyError:
				if (token == cls.EXIT_CHAR):
					if (parserState.Counter == 0):
						parserState.NewToken =  cls.EXIT_TOKEN(token)
						parserState.NewBlock =  cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
						_ =                     cls.EXIT_BLOCK(parserState.NewBlock, parserState.NewToken, endToken=parserState.NewToken)
						parserState.Pop(1)
						return
					else:
						raise BlockParserException("Mismatch in opening and closing parenthesis. Counter={0}".format(parserState.Counter), token)
		elif isinstance(token, CharacterToken):
			if (token == cls.EXIT_CHAR):
				if (parserState.Counter == 0):
					parserState.NewToken =  cls.EXIT_TOKEN(token)
					parserState.NewBlock =  cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
					_ =                     cls.EXIT_BLOCK(parserState.NewBlock, parserState.NewToken, endToken=parserState.NewToken)
					parserState.Pop(2)
					return
				else:
					raise BlockParserException("Mismatch in opening and closing parenthesis. Counter={0}".format(parserState.Counter), token)
			elif (token == "("):
				parserState.NewToken =    OpeningRoundBracketToken(token)
				parserState.Counter +=    1
				parserState.NextState =   cls.stateExpression
				return
			elif (token == ")"):
				if (parserState.Counter == 0):
					parserState.NewToken =    BoundaryToken(token)
					parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)

					parserState.Pop(3, tokenMarker=parserState.NewToken)
					return
				else:
					parserState.NewToken =    ClosingRoundBracketToken(token)
					parserState.Counter -=    1
					parserState.NextState =   cls.stateExpression
					return
			else:
				parserState.NewToken =    cls.CHARACTER_TRANSLATION[token.Value](token)
				parserState.NextState =   cls.stateExpression
				return
		elif isinstance(token, WordToken):
			try:
				parserState.NewToken =    cls.OPERATOR_TRANSLATIONS[token.Value](token)
			except KeyError:
				parserState.NewToken =    IdentifierToken(token)
			parserState.NextState =     cls.stateExpression
			return
		elif isinstance(token, LiteralToken):
			parserState.NextState =     cls.stateExpression
			return
		elif isinstance(token, LinebreakToken):
			if (not (isinstance(parserState.LastBlock, CommentBlock) and isinstance(parserState.LastBlock.StartToken, MultiLineCommentToken))):
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				_ =                       LinebreakBlock(parserState.NewBlock, token)
			else:
				parserState.NewBlock =    LinebreakBlock(parserState.LastBlock, token)
			parserState.TokenMarker =   None
			return
		elif isinstance(token, CommentToken):
			if (not isinstance(parserState.LastBlock, LinebreakBlock)):
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				_ =                       CommentBlock(parserState.NewBlock, token)
			else:
				parserState.NewBlock =    CommentBlock(parserState.LastBlock, token)
			parserState.TokenMarker =   None
			return
		elif (isinstance(token, IndentationToken) and isinstance(token.PreviousToken, (LinebreakToken, SingleLineCommentToken))):
			return
		elif (isinstance(token, SpaceToken) and (isinstance(parserState.LastBlock, CommentBlock) and isinstance(parserState.LastBlock.StartToken, MultiLineCommentToken))):
			parserState.NewToken =      BoundaryToken(token)
			parserState.NewBlock =      WhitespaceBlock(parserState.LastBlock, parserState.NewToken)
			parserState.TokenMarker =   None
			return

		raise BlockParserException("Expected ????????????.", token)


@export
class ExpressionBlockEndedByKeywordORClosingRoundBracket(ExpressionBlock):
	EXIT_KEYWORD =  None
	EXIT_BLOCK =    None

	@classmethod
	def stateExpression(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, FusedCharacterToken):
			parserState.NewToken = cls.FUSED_CHARACTER_TRANSLATION[token.Value](token)
			return
		elif isinstance(token, CharacterToken):
			if (token == "("):
				parserState.NewToken =    OpeningRoundBracketToken(token)
				parserState.Counter +=    1
				return
			elif (token == ")"):
				parserState.NewToken =  ClosingRoundBracketToken(token)
				parserState.Counter -=  1
				return
			else:
				parserState.NewToken =    cls.CHARACTER_TRANSLATION[token.Value](token)
				return
		elif isinstance(token, WordToken):
			if (token <= cls.EXIT_KEYWORD.__KEYWORD__):
				parserState.NewToken =    cls.EXIT_KEYWORD(token)
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
				_ =                       cls.EXIT_BLOCK(parserState.NewBlock, parserState.NewToken)
				parserState.Pop()
				return
			else:
				try:
					parserState.NewToken =    cls.OPERATOR_TRANSLATIONS[token.Value](token)
				except KeyError:
					parserState.NewToken =    IdentifierToken(token)
				return
		elif isinstance(token, LiteralToken):
			return
		elif isinstance(token, SpaceToken):
			parserState.NextState =     cls.stateWhitespace1
			return
		elif isinstance(token, (LinebreakToken, CommentToken)):
			block =                     LinebreakBlock if isinstance(token, LinebreakToken) else CommentBlock
			parserState.NewBlock =      cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
			_ =                         block(parserState.NewBlock, token)
			parserState.TokenMarker =   None
			parserState.NextState =     cls.stateWhitespace1
			return

		raise BlockParserException("Expected '(' or whitespace after keyword GENERIC.", token)

	@classmethod
	def stateWhitespace1(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, FusedCharacterToken):
			parserState.NewToken =    cls.FUSED_CHARACTER_TRANSLATION[token.Value](token)
			parserState.NextState =   cls.stateExpression
			return
		elif isinstance(token, CharacterToken):
			if (token == "("):
				parserState.NewToken =    OpeningRoundBracketToken(token)
				parserState.Counter +=    1
				parserState.NextState =   cls.stateExpression
				return
			elif (token == ")"):
				parserState.NewToken =    ClosingRoundBracketToken(token)
				parserState.Counter -=    1
				parserState.NextState =   cls.stateExpression
				return
			else:
				parserState.NewToken =    cls.CHARACTER_TRANSLATION[token.Value](token)
				parserState.NextState =   cls.stateExpression
				return
		elif isinstance(token, WordToken):
			if (token <= cls.EXIT_KEYWORD.__KEYWORD__):
				parserState.NewToken =    cls.EXIT_KEYWORD(token)
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
				_ =                       cls.EXIT_BLOCK(parserState.NewBlock, parserState.NewToken)
				parserState.Pop()
				return
			else:
				try:
					parserState.NewToken =  cls.OPERATOR_TRANSLATIONS[token.Value](token)
				except KeyError:
					parserState.NewToken =  IdentifierToken(token)
				parserState.NextState =   cls.stateExpression
				return
		elif isinstance(token, LiteralToken):
			parserState.NextState =     cls.stateExpression
			return
		elif isinstance(token, LinebreakToken):
			if (not (isinstance(parserState.LastBlock, CommentBlock) and isinstance(parserState.LastBlock.StartToken, MultiLineCommentToken))):
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				_ =                       LinebreakBlock(parserState.NewBlock, token)
			else:
				parserState.NewBlock =    LinebreakBlock(parserState.LastBlock, token)
			parserState.TokenMarker =   None
			return
		elif isinstance(token, CommentToken):
			if (not isinstance(parserState.LastBlock, LinebreakBlock)):
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				_ =                       CommentBlock(parserState.NewBlock, token)
			else:
				parserState.NewBlock =    CommentBlock(parserState.LastBlock, token)
			parserState.TokenMarker =   None
			return
		elif (isinstance(token, IndentationToken) and isinstance(token.PreviousToken, (LinebreakToken, SingleLineCommentToken))):
			return
		elif (isinstance(token, SpaceToken) and (isinstance(parserState.LastBlock, CommentBlock) and isinstance(parserState.LastBlock.StartToken, MultiLineCommentToken))):
			parserState.NewToken =      BoundaryToken(token)
			parserState.NewBlock =      WhitespaceBlock(parserState.LastBlock, parserState.NewToken)
			parserState.TokenMarker =   None
			return

		raise BlockParserException("Expected ????????????.", token)


@export
class ExpressionBlockEndedByKeywordOrToOrDownto(ExpressionBlock):
	EXIT_KEYWORD =  None
	EXIT_BLOCK =    None

	@classmethod
	def stateExpression(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, FusedCharacterToken):
			parserState.NewToken = cls.FUSED_CHARACTER_TRANSLATION[token.Value](token)
			return
		elif isinstance(token, CharacterToken):
			if (token == "("):
				parserState.NewToken =    OpeningRoundBracketToken(token)
				parserState.Counter +=    1
				return
			elif (token == ")"):
				parserState.NewToken =  ClosingRoundBracketToken(token)
				parserState.Counter -=  1
				return
			else:
				parserState.NewToken =    cls.CHARACTER_TRANSLATION[token.Value](token)
				return
		elif isinstance(token, WordToken):
			tokenValue = token.Value.lower()
			if (tokenValue == cls.EXIT_KEYWORD.__KEYWORD__):
				parserState.NewToken =    LoopKeyword(token)
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
				_ =                       cls.EXIT_BLOCK(parserState.NewBlock, parserState.NewToken)
				parserState.Pop(2, parserState.NewToken)
				return
			elif (tokenValue == "to"):
				from pyVHDLParser.Blocks.ControlStructure.ForLoop import LoopIterationDirectionBlock

				parserState.NewToken =    ToKeyword(token)
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
				_ =                       LoopIterationDirectionBlock(parserState.NewBlock, parserState.NewToken)
				parserState.Pop(1, parserState.NewToken)
				return
			elif (tokenValue == "downto"):
				from pyVHDLParser.Blocks.ControlStructure.ForLoop import LoopIterationDirectionBlock

				parserState.NewToken =    DowntoKeyword(token)
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
				_ =                       LoopIterationDirectionBlock(parserState.NewBlock, parserState.NewToken)
				parserState.Pop(1, parserState.NewToken)
				return
			else:
				try:
					parserState.NewToken =    cls.OPERATOR_TRANSLATIONS[token.Value](token)
				except KeyError:
					parserState.NewToken =    IdentifierToken(token)
				return
		elif isinstance(token, LiteralToken):
			return
		elif isinstance(token, SpaceToken):
			parserState.NextState =     cls.stateWhitespace1
			return
		elif isinstance(token, (LinebreakToken, CommentToken)):
			block =                     LinebreakBlock if isinstance(token, LinebreakToken) else CommentBlock
			parserState.NewBlock =      cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
			_ =                         block(parserState.NewBlock, token)
			parserState.TokenMarker =   None
			parserState.NextState =     cls.stateWhitespace1
			return

		raise BlockParserException("Expected '(' or whitespace after keyword GENERIC.", token)

	@classmethod
	def stateWhitespace1(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, FusedCharacterToken):
			parserState.NewToken =    cls.FUSED_CHARACTER_TRANSLATION[token.Value](token)
			parserState.NextState =   cls.stateExpression
			return
		elif isinstance(token, CharacterToken):
			if (token == "("):
				parserState.NewToken =    OpeningRoundBracketToken(token)
				parserState.Counter +=    1
				parserState.NextState =   cls.stateExpression
				return
			elif (token == ")"):
				parserState.NewToken =  ClosingRoundBracketToken(token)
				parserState.Counter -=  1
				parserState.NextState = cls.stateExpression
				return
			else:
				parserState.NewToken =    cls.CHARACTER_TRANSLATION[token.Value](token)
				parserState.NextState =   cls.stateExpression
				return
		elif isinstance(token, WordToken):
			tokenValue = token.Value.lower()
			if (tokenValue == cls.EXIT_KEYWORD.__KEYWORD__):
				parserState.NewToken =    LoopKeyword(token)
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
				_ =                       cls.EXIT_BLOCK(parserState.NewBlock, parserState.NewToken)
				parserState.Pop(1, parserState.NewToken)
				return
			elif (tokenValue == "to"):
				from pyVHDLParser.Blocks.ControlStructure.ForLoop import LoopIterationDirectionBlock

				parserState.NewToken =    ToKeyword(token)
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
				_ =                       LoopIterationDirectionBlock(parserState.NewBlock, parserState.NewToken)
				parserState.Pop()
				return
			elif (tokenValue == "downto"):
				from pyVHDLParser.Blocks.ControlStructure.ForLoop import LoopIterationDirectionBlock

				parserState.NewToken =    DowntoKeyword(token)
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
				_ =                       LoopIterationDirectionBlock(parserState.NewBlock, parserState.NewToken)
				parserState.Pop()
				return
			else:
				try:
					parserState.NewToken =  cls.OPERATOR_TRANSLATIONS[token.Value](token)
				except KeyError:
					parserState.NewToken =  IdentifierToken(token)
				parserState.NextState =   cls.stateExpression
				return
		elif isinstance(token, LiteralToken):
			parserState.NextState =     cls.stateExpression
			return
		elif isinstance(token, LinebreakToken):
			if (not (isinstance(parserState.LastBlock, CommentBlock) and isinstance(parserState.LastBlock.StartToken, MultiLineCommentToken))):
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				_ =                       LinebreakBlock(parserState.NewBlock, token)
			else:
				parserState.NewBlock =    LinebreakBlock(parserState.LastBlock, token)
			parserState.TokenMarker =   None
			return
		elif isinstance(token, CommentToken):
			if (not isinstance(parserState.LastBlock, LinebreakBlock)):
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				_ =                       CommentBlock(parserState.NewBlock, token)
			else:
				parserState.NewBlock =    CommentBlock(parserState.LastBlock, token)
			parserState.TokenMarker =   None
			return
		elif (isinstance(token, IndentationToken) and isinstance(token.PreviousToken, (LinebreakToken, SingleLineCommentToken))):
			return
		elif (isinstance(token, SpaceToken) and (isinstance(parserState.LastBlock, CommentBlock) and isinstance(parserState.LastBlock.StartToken, MultiLineCommentToken))):
			parserState.NewToken =      BoundaryToken(token)
			parserState.NewBlock =      WhitespaceBlock(parserState.LastBlock, parserState.NewToken)
			parserState.TokenMarker =   None
			return

		raise BlockParserException("Expected ????????????.", token)


@export
class ExpressionBlockEndedBySemicolon(ExpressionBlock):
	END_BLOCK = None

	@classmethod
	def stateExpression(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, FusedCharacterToken):
			parserState.NewToken = cls.FUSED_CHARACTER_TRANSLATION[token.Value](token)
			return
		elif isinstance(token, CharacterToken):
			if (token == ";"):
				if (parserState.Counter == 0):
					parserState.NewToken =  EndToken(token)
					parserState.NewBlock =  cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
					_ =                     cls.END_BLOCK(parserState.NewBlock, parserState.NewToken, endToken=parserState.NewToken)
					parserState.Pop(2)
					return
				else:
					raise BlockParserException("Mismatch in opening and closing parenthesis. Counter={0}".format(parserState.Counter), token)
			elif (token == "("):
				parserState.NewToken =    OpeningRoundBracketToken(token)
				parserState.Counter +=    1
				return
			elif (token == ")"):
				if (parserState.Counter == -1):
					raise BlockParserException("Mismatch in opening and closing parenthesis. Counter={0}".format(parserState.Counter), token)
				else:
					parserState.NewToken =  ClosingRoundBracketToken(token)
					parserState.Counter -=  1
					return
			else:
				parserState.NewToken =    cls.CHARACTER_TRANSLATION[token.Value](token)
				return
		elif isinstance(token, WordToken):
			try:
				parserState.NewToken =    cls.OPERATOR_TRANSLATIONS[token.Value](token)
			except KeyError:
				parserState.NewToken =    IdentifierToken(token)
			return
		elif isinstance(token, LiteralToken):
			return
		elif isinstance(token, SpaceToken):
			parserState.NextState =     cls.stateWhitespace1
			return
		elif isinstance(token, (LinebreakToken, CommentToken)):
			block =                     LinebreakBlock if isinstance(token, LinebreakToken) else CommentBlock
			parserState.NewBlock =      cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
			_ =                         block(parserState.NewBlock, token)
			parserState.TokenMarker =   None
			parserState.NextState =     cls.stateWhitespace1
			return

		raise BlockParserException("Expected operator, '(', ')', ';' or whitespace.", token)

	@classmethod
	def stateWhitespace1(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, FusedCharacterToken):
			parserState.NewToken =    cls.FUSED_CHARACTER_TRANSLATION[token.Value](token)
			parserState.NextState =   cls.stateExpression
			return
		elif isinstance(token, CharacterToken):
			if (token == ";"):
				if (parserState.Counter == 0):
					parserState.NewToken =  EndToken(token)
					parserState.NewBlock =  cls(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
					_ =                     cls.END_BLOCK(parserState.NewBlock, parserState.NewToken, endToken=parserState.NewToken)
					parserState.Pop(2)
					return
				else:
					raise BlockParserException("Mismatch in opening and closing parenthesis. Counter={0}".format(parserState.Counter), token)
			elif (token == "("):
				parserState.NewToken =    OpeningRoundBracketToken(token)
				parserState.Counter +=    1
				parserState.NextState =   cls.stateExpression
				return
			elif (token == ")"):
				if (parserState.Counter == -1):
					raise BlockParserException("Mismatch in opening and closing parenthesis. Counter={0}".format(parserState.Counter), token)
				else:
					parserState.NewToken =  ClosingRoundBracketToken(token)
					parserState.Counter -=  1
					parserState.NextState = cls.stateExpression
					return
			else:
				parserState.NewToken =    cls.CHARACTER_TRANSLATION[token.Value](token)
				parserState.NextState =   cls.stateExpression
				return
		elif isinstance(token, WordToken):
			try:
				parserState.NewToken =    cls.OPERATOR_TRANSLATIONS[token.Value](token)
			except KeyError:
				parserState.NewToken =    IdentifierToken(token)
			parserState.NextState =     cls.stateExpression
			return
		elif isinstance(token, LiteralToken):
			parserState.NextState =     cls.stateExpression
			return
		elif isinstance(token, LinebreakToken):
			if (not (isinstance(parserState.LastBlock, CommentBlock) and isinstance(parserState.LastBlock.StartToken, MultiLineCommentToken))):
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				_ =                       LinebreakBlock(parserState.NewBlock, token)
			else:
				parserState.NewBlock =    LinebreakBlock(parserState.LastBlock, token)
			parserState.TokenMarker =   None
			return
		elif isinstance(token, CommentToken):
			if (not isinstance(parserState.LastBlock, LinebreakBlock)):
				parserState.NewBlock =    cls(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				_ =                       CommentBlock(parserState.NewBlock, token)
			else:
				parserState.NewBlock =    CommentBlock(parserState.LastBlock, token)
			parserState.TokenMarker =   None
			return
		elif (isinstance(token, IndentationToken) and isinstance(token.PreviousToken, (LinebreakToken, SingleLineCommentToken))):
			return
		elif (isinstance(token, SpaceToken) and (isinstance(parserState.LastBlock, CommentBlock) and isinstance(parserState.LastBlock.StartToken, MultiLineCommentToken))):
			parserState.NewToken =      BoundaryToken(token)
			parserState.NewBlock =      WhitespaceBlock(parserState.LastBlock, parserState.NewToken)
			parserState.TokenMarker =   None
			return

		raise BlockParserException("Expected identifier, literal, operator, '(', ')' or ';'.", token)
