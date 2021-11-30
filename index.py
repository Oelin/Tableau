unconsumed = ''


def feed(string):
    global unconsumed

    unconsumed = string


def match(characters):
    start = unconsumed[0]

    if unconsumed and (start in characters):
        feed(unconsumed[1:])

        return start

    raise SyntaxError()


def _(parser, *args):
    current = unconsumed

    try:
        return parser(*args)
    except:
        feed(current)


class AstNode:
    def __init__(self, **props):
        self.__dict__ = props

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return unparse(self)


# parsers

def Lbrace():
    return match('(')


def Rbrace():
    return match(')')


def Comma():
    return match(',')


def Variable():
    return match('xyzw')


def Predicate():
    return match('PQRS')


def Operator():
    return match('^v>')


def Literal():

    return AstNode(
      type = 'Literal',
      value = match('pqrs')
    )


def Sentence():

    redicate = Predicate()
    Lbrace()
    first = Variable()
    Comma()
    second = Variable()
    Rbrace()

    return AstNode(
      type = 'Sentence',
      predicate = predicate,
      first = first,
      second = second
    )


def Quantified():

    return AstNode(
      type = 'Quantified',
      kind = match('AE'),
      variable = Variable(),
      right = Proposition()
    )


def Unary():

    return AstNode(
      type = 'Unary',
      operator = match('-'),
      right = Proposition()
    )


def Binary():

    Lbrace()
    left = Proposition()
    operator = Operator()
    right = Proposition()
    Rbrace()

    return AstNode(
      type = 'Binary',
      operator = operator,
      left = left,
      right = right
    )


def Proposition():
    return _(Literal) or _(Sentence) or _(Unary) or _(Quantified) or Binary()


def parse(string):
    feed(string)

    return Proposition()


# pattern matchers - ugly now, more readable later

AstNode.isLiteral = lambda node: node.type == 'Literal'
AstNode.isNegation = lambda node: node.type == 'Unary' and node.operator == '-'
AstNode.isConjunction = lambda node: node.type == 'Binary' and node.operator == '^'
AstNode.isDisjunction = lambda node: node.type == 'Binary' and node.operator == 'v'
AstNode.isImplication = lambda node: node.type == 'Binary' and node.operator == '>'
AstNode.isNegatedLiteral = lambda node: node.isNegation() and node.right.isLiteral()
AstNode.isDoubleNegation = lambda node: node.isNegation() and node.right.isNegation()
AstNode.isNegatedConjunction = lambda node: node.isNegation() and node.right.isConjunction()
AstNode.isNegatedDisjunction = lambda node: node.isNegation() and node.right.isDisjunction()
AstNode.isNegatedImplication = lambda node: node.isNegation() and node.right.isImplication()
AstNode.isCompound = lambda node: not (node.isLiteral() or node.isNegatedLiteral())
AstNode.negate = lambda node: AstNode(type='Unary', operator='-', right=node)


# a paragraph is a set of propositions

class Paragraph(set):

    def __init__(self, nodes):
        super().__init__(nodes)


    def isExpanded(self):
        return not self.pickCompound()


    def isContradictory(self):
        positive = set()
        negative = set()

        for node in self:
            if node.isLiteral(): positive.add(node.value)
            if node.isNegatedLiteral(): negative.add(node.right.value)

        return len(positive & negative) > 0


    def pickCompound(self):
        for node in self:
            if node.isCompound(): return node


# tableu data structure

class Tableau(list):

    def __init__(self, root):
        super().__init__([ Paragraph({ root }) ])

    def push(self, paragraph):
        if not paragraph.isContradictory():
            self.append(paragraph)

    def pushAlpha(self, paragraph, left, right):
        paragraph.add(left)
        paragraph.add(right)

        self.push(paragraph)

    def pushBeta(self, paragraph, left, right):
        lhs = Paragraph(paragraph)
        rhs = Paragraph(paragraph)

        lhs.add(left)
        rhs.add(right)

        self.push(lhs)
        self.push(rhs)


# tableau algorithm

def checkSatisfiable(node):
    tab = Tableau(node)

    while tab:
        paragraph = tab.pop()

        if paragraph.isExpanded() and not paragraph.isContradictory():
            return True

        else:
            nonlit = paragraph.pickCompound()
            paragraph.remove(nonlit)

            # alpha

            if nonlit.isConjunction():
                tab.pushAlpha(paragraph, nonlit.left, nonlit.right)

            elif nonlit.isDoubleNegation():
                paragraph.add(nonlit.right.right)
                tab.push(paragraph)

            elif nonlit.isNegatedDisjunction():
                tab.pushAlpha(paragraph, nonlit.right.left.negate(), nonlit.right.right.negate())

            elif nonlit.isNegatedImplication():
                tab.pushAlpha(paragraph, nonlit.right.left, nonlit.right.right.negate())

            # beta

            elif nonlit.isDisjunction():
                tab.pushBeta(paragraph, nonlit.left, nonlit.right)

            elif nonlit.isNegatedConjunction():
                tab.pushBeta(paragraph, nonlit.right.left.negate(), nonlit.right.right.negate())

            elif nonlit.isImplication():
                tab.pushBeta(paragraph, nonlit.left.negate(), nonlit.right)

    return False
