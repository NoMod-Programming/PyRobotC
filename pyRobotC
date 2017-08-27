import ast
import sys

class CPrinter(object):
  @classmethod
  def c_imports(self, aNode):
    asC = '#include "'
    asC += aNode.names[0].name + '"'
    return asC
  
  @classmethod
  def module_to_c(self, aNode):
    if isinstance(aNode, ast.Expr):
      aNode = aNode.value
    if self.c_fornode(aNode.func) == 'vex.pragma':
      asC = '#pragma '
      useComma = False
      pragmaDirective = aNode.args.pop(0)
      asC += self.c_fornode(pragmaDirective)
      if aNode.args:
        asC += '('
        for arg in aNode.args:
          if useComma:
            asC += ', '
          else:
            useComma = True
          asC += self.c_fornode(arg)
        asC += ')'
      return asC
    elif self.c_fornode(aNode.func) == 'cfuncs.unused':
      return ''
    return 'nil'

  @classmethod
  def c_string(self, s, max_length = 509, unicode=False):
    ret = []

    # Try to split on whitespace, not in the middle of a word.
    split_at_space_pos = max_length - 10
    if split_at_space_pos < 10:
        split_at_space_pos = None

    position = 0
    if unicode:
        position += 1
        ret.append('L')

    ret.append('"')
    position += 1
    for c in s:
        newline = False
        if c == "\n":
            to_add = r"\n"
            newline = True
        elif ord(c) < 32 or 0x80 <= ord(c) <= 0xff:
            to_add = r"\x{:02X}".format(ord(c))
        elif ord(c) > 0xff:
            if not unicode:
                raise ValueError("string contains unicode character but unicode=False")
            to_add = r"\u{:04X}".format(ord(c))
        elif r'\"'.find(c) != -1:
            to_add = r"\{}".format(c)
        else:
            to_add = c

        ret.append(to_add)
        position += len(to_add)
        if newline:
            position = 0

        if split_at_space_pos is not None and position >= split_at_space_pos and " \t".find(c) != -1:
            ret.append("\\\n")
            position = 0
        elif position >= max_length:
            ret.append("\\\n")
            position = 0

    ret.append('"')

    return "".join(ret)

  @classmethod
  def literal(self,aNode):
    if isinstance(aNode, ast.Num):
      return str(aNode.n)
    elif isinstance(aNode, ast.Str):
      return self.c_string(aNode.s)
    elif isinstance(aNode, ast.Bytes):
      return self.c_string(aNode.s.decode('utf-8'))

  @classmethod
  def functionHeader(self, aNode):
    # Print function header (`int main(args) {`)
    asC = aNode.returns.id + ' ' + aNode.name + '('
    isFirst = True
    for i, arg in enumerate(aNode.args.args):
      if isFirst:
        isFirst = False
      else:
        asC += ', '
      asC += arg.annotation.id + ' ' + arg.arg
      if i >= len(aNode.args.args) - len(aNode.args.defaults):
        asC += ' = ' + self.literal(aNode.args.defaults[i - (len(aNode.args.args) - len(aNode.args.defaults))])
    asC += ') {\n'
    return asC
    
  @classmethod
  def if_while_c(self, aNode, indent):
    if isinstance(aNode, ast.If):
      asC = 'if ('
    else:
      asC = 'while ('
    asC += self.c_fornode(aNode.test)
    asC += ') {\n'
    for statement in aNode.body:
      asC += self.c_fornode(statement,indent + 2) # Print with indent
      asC += ';\n' # Add semicolon and newline
    asC += ' ' * indent + '}'
    if aNode.orelse:
      asC += ' else {\n'
      for statement in aNode.orelse:
        asC += self.c_fornode(statement, indent + 2) # Print with indent
        asC += ';\n'
      asC += ' ' * indent + '}'
    return asC
    
  @classmethod
  def forloop_c(self, aNode, indent):
    asC = ''
    if isinstance(aNode.iter, ast.Call):
      if aNode.iter.func.id == 'range':
        # for [] in range(low,high,[step])
        var = self.variable(aNode.target)
        low = '0'
        step = '1'
        if len(aNode.iter.args) > 1:
          low = self.c_fornode(aNode.iter.args[0])
          high = self.c_fornode(aNode.iter.args[1])
          if len(aNode.iter.args) > 2:
            step = self.c_fornode(aNode.iter.args[2])
        else:
          high = self.c_fornode(aNode.iter.args[0])
        asC += 'for (' + var + ' = '
        asC += low
        asC += '; ' + var + ' < ' + high + '; ' + var + ' += ' + step + ') {\n'
    for statement in aNode.body:
      asC += self.c_fornode(statement,indent + 2) # Print with indent
      asC += ';\n' # Add semicolon and newline
    asC += ' ' * indent + '}'
    return asC
    
  @classmethod
  def c_fornode(self, aNode, indent=0):
    asC = ' ' * indent
    if isinstance(aNode, (ast.Num, ast.Str, ast.Bytes)):
      asC += self.literal(aNode)
    elif isinstance(aNode, (ast.Expr, ast.Return, ast.Call)):
      asC += self.method(aNode)
    elif isinstance(aNode, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Delete, ast.Name, ast.NameConstant, ast.Subscript, ast.Attribute)):
      asC += self.variable(aNode)
    elif isinstance(aNode, ast.BinOp):
      asC += self.binop_c(aNode)
    elif isinstance(aNode, ast.Compare):
      asC += self.compare_c(aNode)
    elif isinstance(aNode, (ast.If, ast.While)):
      asC += self.if_while_c(aNode, indent)
    elif isinstance(aNode, ast.IfExp):
      asC += self.inline_if(aNode)
    elif isinstance(aNode, ast.For):
      asC += self.forloop_c(aNode, indent)
    elif isinstance(aNode, (ast.Continue, ast.Break)):
      asC += self.controlflow(aNode)
    elif isinstance(aNode, ast.Pass):
      pass # Ironic, but we don't need to do anything anyways
    elif isinstance(aNode, ast.FunctionDef):
      asC += self.function(aNode)
    elif isinstance(aNode, ast.Import):
      asC += self.c_imports(aNode)
    return asC
  
  @classmethod
  def inline_if(self, aNode):
    asC = '(' + self.c_fornode(aNode.test) + ' ? '
    asC += self.c_fornode(aNode.body)
    asC += ' : ' + self.c_fornode(aNode.orelse) + ')'
    return asC
  
  @classmethod
  def compare_c(self, aNode):
    asC = ''
    doAnd = False
    allValues = aNode.comparators
    allValues.insert(0,aNode.left)
    for i,op in enumerate(aNode.ops):
      if doAnd:
        asC += ' && '
      else:
        doAnd = True
      asC += '(' + self.c_fornode(allValues[i])
      asC += ' ' + self.compare(op) + ' '
      asC += self.c_fornode(allValues[i + 1]) + ')'
    return asC
      
  @classmethod
  def controlflow(self, aNode):
    if isinstance(aNode, ast.Break):
      return 'break'
    elif isinstance(aNode, ast.Continue):
      return 'continue'
  
  @classmethod
  def compare(self, aNode):
    if isinstance(aNode, ast.Eq):
      return '=='
    elif isinstance(aNode, ast.NotEq):
      return '!='
    elif isinstance(aNode, ast.Lt):
      return '<'
    elif isinstance(aNode, ast.LtE):
      return '<='
    elif isinstance(aNode, ast.Gt):
      return '>'
    elif isinstance(aNode, ast.GtE):
      return '>='
  
  @classmethod
  def binop_c(self, aNode):
    asC = '(' + self.c_fornode(aNode.left)
    asC += ' ' + self.binop(aNode.op) + ' '
    asC += self.c_fornode(aNode.right) + ')'
    return asC
  
  @classmethod
  def binop(self, aNode):
    if isinstance(aNode, ast.Add):
      return '+'
    elif isinstance(aNode, ast.Sub):
      return '-'
    elif isinstance(aNode, ast.Mult):
      return '*'
    elif isinstance(aNode, ast.Div):
      return '/'
    elif isinstance(aNode, ast.Mod):
      return '%'
    elif isinstance(aNode, ast.LShift):
      return '<<'
    elif isinstance(aNode, ast.RShift):
      return '>>'
    elif isinstance(aNode, ast.BitOr):
      return '|'
    elif isinstance(aNode, ast.BitXor):
      return '^'
    elif isinstance(aNode, ast.BitAnd):
      return '&'
  
  @classmethod
  def variable(self, aNode):
    asC = ''
    if isinstance(aNode, ast.Assign):
      for target in aNode.targets:
        asC += self.c_fornode(target) + ' = '
      asC += self.c_fornode(aNode.value)
    elif isinstance(aNode, ast.AnnAssign):
      asC += aNode.annotation.id + ' ' + self.c_fornode(aNode.target)
      if aNode.value:
        asC += ' = ' + self.c_fornode(aNode.value)
    elif isinstance(aNode, ast.AugAssign):
      asC += self.c_fornode(aNode.target)
      asC += ' ' + self.binop(aNode.op) + '= '
      asC += self.c_fornode(aNode.value)
    elif isinstance(aNode, ast.Delete):
      raise SyntaxError("del [var] is not supported in C!")
    elif isinstance(aNode, ast.Name):
      asC += aNode.id
    elif isinstance(aNode, ast.NameConstant):
      if aNode.value == True:
        return '1'
      elif aNode.value == False:
        return '0'
      elif aNode.value == None:
        return '0'
    elif isinstance(aNode, ast.Subscript):
      asC += self.c_fornode(aNode.value) + '['
      asC += self.c_fornode(aNode.slice.value)
      asC += ']'
    elif isinstance(aNode, ast.Attribute):
      asC += self.c_fornode(aNode.value) + '.'
      asC += aNode.attr
    return asC
  
  @classmethod
  def method(self, aNode):
    asC = ''
    if isinstance(aNode,ast.Expr):
      if isinstance(aNode.value, ast.Name):
        asC += aNode.value.id
        return asC
      if 'id' in aNode.value.func.__dict__:
        asC += aNode.value.func.id + '('
      else:
        if aNode.value.func.value.id in ['vex','cfuncs']:
          return self.module_to_c(aNode)
        asC += aNode.value.func.value.id + '.' + aNode.value.func.attr + '('
      useComma = False
      for argNode in aNode.value.args:
        if useComma:
          asC += ', '
        else:
          useComma = True
        asC += self.c_fornode(argNode)
      asC += ')'
    elif isinstance(aNode, ast.Return):
      asC += 'return ' + self.c_fornode(aNode.value)
    elif isinstance(aNode, ast.Call):
      if 'value' in aNode.func.__dict__:
        if aNode.func.value.id in ['vex','cfuncs']:
          return self.module_to_c(aNode)
      asC += self.c_fornode(aNode.func) + '('
      useComma = False
      for argNode in aNode.args:
        if useComma:
          asC += ', '
        else:
          useComma = True
        asC += self.c_fornode(argNode)
      asC += ')'
    return asC
  
  @classmethod
  def function(self, aNode):
    # Print multiling docstring
    asC = '\n\n'
    if ast.get_docstring(aNode):
      asC += '/*\n'
      asC += ast.get_docstring(aNode)
      aNode.body.pop(0)
      asC += '\n*/\n'
    asC += self.functionHeader(aNode)
    # Print the methods in the function
    for statement in aNode.body:
      asC += self.c_fornode(statement,2) # Print method with indent of 2
      asC += ';\n' # Add semicolon and newline
    # Close the function
    asC += '}'
    return asC
    
  @classmethod
  def printcfor(self, aNode):
    if isinstance(aNode, ast.FunctionDef):
      return self.function(aNode)
    else:
      return self.c_fornode(aNode) + ';'
if __name__ == '__main__':
  if len(sys.argv) < 2:
    sys.argv.append('vexCode.py')
    if input("Use default file vexCode.py? [Y/N] ").lower() == 'n':
      sys.exit(1)
  for item in ast.parse(open(sys.argv[1],'r').read(),mode='exec').body:
    print(CPrinter.printcfor(item))
