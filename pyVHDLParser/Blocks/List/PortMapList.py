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
from pydecor.decorators               import export

from pyVHDLParser.Token               import CharacterToken, SpaceToken, WordToken, LinebreakToken, IndentationToken
from pyVHDLParser.Token.Keywords      import BoundaryToken, IdentifierToken, EndToken, DelimiterToken, OpeningRoundBracketToken, ClosingRoundBracketToken
from pyVHDLParser.Blocks              import BlockParserException, Block, ParserState, SkipableBlock
from pyVHDLParser.Blocks.Common       import LinebreakBlock, IndentationBlock, WhitespaceBlock
from pyVHDLParser.Blocks.Comment      import SingleLineCommentBlock, MultiLineCommentBlock

__all__ = []
__api__ = __all__


@export
class OpenBlock(Block):
	@classmethod
	def statePortKeyword(cls, parserState: ParserState):
		token = parserState.Token
		errorMessage = "Expected whitespace or '(' after keyword PORT."
		if isinstance(token, CharacterToken):
			if (token == "("):
				parserState.NewToken =    BoundaryToken(token)
				parserState.NewBlock =    OpenBlock(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken)
				parserState.NextState =   CloseBlock.stateClosingParenthesis
				parserState.PushState =   OpenBlock.stateOpeningParenthesis
				parserState.Counter =     1
				return
			elif (token == "\n"):
				parserState.NewBlock =    OpenBlock(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				parserState.NewToken =    LinebreakToken(token)
				_ =                       LinebreakBlock(parserState.NewBlock, parserState.NewToken)
				parserState.TokenMarker = None
				parserState.NextState =   cls.stateWhitespace1
				parserState.PushState =   LinebreakBlock.stateLinebreak
				return
			elif (token == "-"):
				parserState.NewBlock =    OpenBlock(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				parserState.TokenMarker = None
				parserState.NextState =   cls.stateWhitespace1
				parserState.PushState =   SingleLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
			elif (token == "/"):
				parserState.NewBlock =    OpenBlock(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				parserState.TokenMarker = None
				parserState.NextState =   cls.stateWhitespace1
				parserState.PushState =   MultiLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
		elif isinstance(token, SpaceToken):
			parserState.NextState =     cls.stateWhitespace1
			return

		raise BlockParserException(errorMessage, token)

	@classmethod
	def stateWhitespace1(cls, parserState: ParserState):
		token = parserState.Token

		errorMessage = "Expected  '(' after keyword PORT."
		if isinstance(token, CharacterToken):
			if (token == "("):
				parserState.NewToken =    BoundaryToken(token)
				parserState.NewBlock =    OpenBlock(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken)
				parserState.NextState =   CloseBlock.stateClosingParenthesis
				parserState.PushState =   OpenBlock.stateOpeningParenthesis
				parserState.Counter =     1
				return
			elif (token == "\n"):
				parserState.NewToken =    LinebreakToken(token)
				if (not isinstance(parserState.LastBlock, MultiLineCommentBlock)):
					parserState.NewBlock =  OpenBlock(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken, multiPart=True)
					_ =                     LinebreakBlock(parserState.NewBlock, parserState.NewToken)
				else:
					parserState.NewBlock =  LinebreakBlock(parserState.LastBlock, parserState.NewToken)
				parserState.TokenMarker = None
				parserState.NextState =   cls.stateWhitespace1
				parserState.PushState =   LinebreakBlock.stateLinebreak
				return
			elif (token == "-"):
				parserState.NewBlock =    OpenBlock(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				parserState.TokenMarker = None
				parserState.NextState =   cls.stateWhitespace1
				parserState.PushState =   SingleLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
			elif (token == "/"):
				parserState.NewBlock =    OpenBlock(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				parserState.TokenMarker = None
				parserState.NextState =   cls.stateWhitespace1
				parserState.PushState =   MultiLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
		elif (isinstance(token, SpaceToken) and isinstance(parserState.LastBlock, MultiLineCommentBlock)):
			parserState.NewToken =      BoundaryToken(token)
			parserState.NewBlock =      WhitespaceBlock(parserState.LastBlock, parserState.NewToken)
			parserState.TokenMarker =   None
			return

		raise BlockParserException(errorMessage, token)

	@classmethod
	def stateOpeningParenthesis(cls, parserState: ParserState):
		token = parserState.Token
		errorMessage = "Expected port name (identifier)."
		if isinstance(token, CharacterToken):
			if (token == ")"):
				# if (parserState.TokenMarker != token):
				# 	parserState.NewBlock = IndentationBlock(parserState.LastBlock, parserState.TokenMarker, token.PreviousToken)
				parserState.Pop(1, token)
				return
			elif (token == "\n"):
				parserState.NewToken =    LinebreakToken(token)
				parserState.NewBlock =    LinebreakBlock(parserState.LastBlock, parserState.NewToken)
				parserState.TokenMarker = None
				parserState.PushState =   LinebreakBlock.stateLinebreak
				return
			elif (token == "-"):
				parserState.TokenMarker = None
				parserState.PushState =   SingleLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
			elif (token == "/"):
				parserState.TokenMarker = None
				parserState.PushState =   MultiLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
		elif isinstance(token, SpaceToken):
			parserState.NewToken =      IndentationToken(token)
			parserState.NewBlock =      IndentationBlock(parserState.LastBlock, parserState.NewToken)
			return
		elif isinstance(token, WordToken):
			parserState.NewToken =      IdentifierToken(token)
			parserState.TokenMarker =   parserState.NewToken
			parserState.NextState =     ItemBlock.stateItemRemainder

			# if (parserState.TokenMarker != token):
			# 	parserState.NewBlock = IndentationBlock(parserState.LastBlock, parserState.TokenMarker, token)
			return

		raise BlockParserException(errorMessage, token)


@export
class ItemBlock(Block):
	@classmethod
	def stateItemRemainder(cls, parserState: ParserState):
		token = parserState.Token
		if isinstance(token, CharacterToken):
			if (token == "("):
				parserState.NewToken =      OpeningRoundBracketToken(token)
				parserState.Counter += 1
			elif (token == ")"):
				parserState.Counter -= 1
				if (parserState.Counter == 0):
					parserState.NewToken =    BoundaryToken(token)
					parserState.NewBlock =    ItemBlock(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
					parserState.Pop()
					parserState.TokenMarker = parserState.NewToken
				else:
					parserState.NewToken =    ClosingRoundBracketToken(token)
			elif (token == ";"):
				if (parserState.Counter == 1):
					parserState.NewToken = DelimiterToken(token)
					parserState.NewBlock = ItemBlock(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken.PreviousToken)
					_ = DelimiterBlock(parserState.NewBlock, parserState.NewToken)
					parserState.NextState = DelimiterBlock.stateItemDelimiter
				else:
					raise BlockParserException("Mismatch in opening and closing parenthesis: open={0}".format(parserState.Counter), token)


@export
class DelimiterBlock(SkipableBlock):
	def __init__(self, previousBlock, startToken):
		super().__init__(previousBlock, startToken, startToken)

	@classmethod
	def stateItemDelimiter(cls, parserState: ParserState):
		token = parserState.Token
		errorMessage = "Expected port name (identifier)."

		if (isinstance(token, CharacterToken) and (token == "\n")):
			parserState.NewToken =      LinebreakToken(token)
			parserState.NewBlock =      LinebreakBlock(parserState.LastBlock, parserState.NewToken)
			parserState.TokenMarker =   None
			parserState.NextState =     OpenBlock.stateOpeningParenthesis
			parserState.PushState =     LinebreakBlock.stateLinebreak
			return
		elif isinstance(token, SpaceToken):
			parserState.NextState =     OpenBlock.stateOpeningParenthesis
			return
		elif isinstance(token, WordToken):
			parserState.NewToken =      IdentifierToken(token)
			parserState.TokenMarker =   parserState.NewToken
			parserState.NextState =     ItemBlock.stateItemRemainder
			return

		raise BlockParserException(errorMessage, token)


@export
class CloseBlock(Block):
	@classmethod
	def stateClosingParenthesis(cls, parserState: ParserState):
		token = parserState.Token
		errorMessage = "Expected ';' or whitespace."
		if isinstance(token, CharacterToken):
			if (token == ";"):
				parserState.NewToken =    EndToken(token)
				parserState.NewBlock =    CloseBlock(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken)
				parserState.Pop()
				return
			elif (token == "\n"):
				parserState.NewToken =    LinebreakToken(token)
				parserState.PushState =   LinebreakBlock.stateLinebreak
				parserState.TokenMarker = parserState.NewToken
				return
			elif (token == "-"):
				parserState.NewBlock =    CloseBlock(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				parserState.TokenMarker = None
				parserState.NextState =   cls.stateWhitespace1
				parserState.PushState =   SingleLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
			elif (token == "/"):
				parserState.NewBlock =    CloseBlock(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				parserState.TokenMarker = None
				parserState.NextState =   cls.stateWhitespace1
				parserState.PushState =   MultiLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
		elif isinstance(token, SpaceToken):
			parserState.NextState = cls.stateWhitespace1
			return

		raise BlockParserException(errorMessage, token)

	@classmethod
	def stateWhitespace1(cls, parserState: ParserState):
		token = parserState.Token
		errorMessage = "Expected ';'."
		if isinstance(token, CharacterToken):
			if (token == ";"):
				parserState.NewToken =    EndToken(token)
				parserState.NewBlock =    CloseBlock(parserState.LastBlock, parserState.TokenMarker, endToken=parserState.NewToken)
				parserState.Pop()
				return
			elif (token == "\n"):
				# TODO: review this linebreak case
				parserState.NewToken =    LinebreakToken(token)
				parserState.PushState =   LinebreakBlock.stateLinebreak
				parserState.TokenMarker = parserState.NewToken
				return
			elif (token == "-"):
				parserState.NewBlock =    CloseBlock(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				parserState.TokenMarker = None
				parserState.PushState =   SingleLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
			elif (token == "/"):
				parserState.NewBlock =    CloseBlock(parserState.LastBlock, parserState.TokenMarker, endToken=token.PreviousToken, multiPart=True)
				parserState.TokenMarker = None
				parserState.PushState =   MultiLineCommentBlock.statePossibleCommentStart
				parserState.TokenMarker = token
				return
		elif (isinstance(token, SpaceToken) and isinstance(parserState.LastBlock, MultiLineCommentBlock)):
			parserState.NewToken =      BoundaryToken(token)
			parserState.NewBlock =      WhitespaceBlock(parserState.LastBlock, parserState.NewToken)
			parserState.TokenMarker =   None
			return

		raise BlockParserException(errorMessage, token)
