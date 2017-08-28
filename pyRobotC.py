import ast
import traceback
import os
import sys

userFunctions = {}
renames = ['vex.pragma','vex.motor','vex.slaveMotors','vex.motorReversed']
classNames = []
indent = '  '
sameLineBraces = True

compiled = {}

def module_rename(aNode):
  if aNode.func.print_c() == 'vex.pragma':
      asC = '#pragma '
      useComma = False
      pragmaDirective = aNode.args.pop(0)
      asC += pragmaDirective.s
      if aNode.args:
        asC += '('
        for arg in aNode.args:
          if useComma:
            asC += ', '
          else:
            useComma = True
          asC += arg.print_c()
        asC += ')'
      asC += '\n'
      return asC
  elif aNode.func.print_c() == 'vex.motor':
    asC = 'motor[' + aNode.args[0].print_c()
    asC += '] = ' + aNode.args[1].print_c()
    return asC
  elif aNode.func.print_c() == 'vex.slaveMotors':
    masterMotor = aNode.args.pop(0).print_c()
    asC = ''
    for slave in aNode.args:
      asC += 'slaveMotor(' + slave.print_c() + ', ' + masterMotor + ');\n'
    return asC[:-2]
  elif aNode.func.print_c() == 'vex.motorReversed':
    asC = 'bMotorReflected[' + aNode.args[0].print_c()
    asC += '] = ' + aNode.args[1].print_c()
    return asC
  return 'Unknown function. This should not happen'

def escape_string(s, unicode = False, max_length = 200):
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
    
class C_Module(ast.Module):
  def prepare(self):
    pass
  
  def print_c(self):
    asC = ''
    for node in self.body:
      try:
        asC += node.print_c()
      except Exception as e:
        print(traceback.format_exc())
        print("Current code:")
        print(asC)
    return asC
    
class C_Bytes(ast.Bytes):
  def prepare(self):
    pass
  
  def print_c(self):
    return escape_string(self.s.decode('utf-8'),True)

class C_Str(ast.Str):
  def prepare(self):
    pass
  
  def print_c(self):
    return escape_string(self.s)

class C_Num(ast.Num):
  def prepare(self):
    pass
  
  def print_c(self):
    return str(self.n)

class C_FunctionDef(ast.FunctionDef):
  def prepare(self):
    """Prepare for writing. Take note of return types, class names, etc..."""
    if self.returns:
      userFunctions[self.name] = self.returns.print_c()

  def print_c(self):
    asC = '\n'
    if ast.get_docstring(self):
      asC += '/*\n'
      asC += ast.get_docstring(self)
      self.body.pop(0)
      asC += '\n*/\n'
    asC += self.returns.id + ' ' + self.name + '('
    isFirst = True
    for i, argNode in enumerate(self.args.args):
      arg = argNode.arg
      try:
        argType = argNode.annotation.print_c()
      except:
        argType = argNode.annotation
      if isFirst:
        isFirst = False
      else:
        asC += ', '
      asC += argType + ' ' + arg
      if i >= self.args.minArgs:
        asC += ' = ' + (self.args.defaults[i - self.args.minArgs]).print_c()
    if sameLineBraces:
      asC += ') {\n'
    else:
      asC += ')\n{\n'
    for childNode in self.body:
      try:
        unindented = childNode.print_c()
        unindented = '\n'.join([indent + x for x in unindented.split('\n')])
        if not unindented.endswith('}'):
          unindented += ';'
        unindented += '\n'
        asC += unindented
      except Exception as e:
        print(traceback.format_exc())
        print(ast.dump(childNode))
        return asC
    asC += '}\n'
    return asC
    
class C_arguments(ast.arguments):
  def prepare(self):
    self.minArgs = len(self.args) - len(self.defaults)
    self.maxArgs = len(self.args)
  
  def print_c(self):
    return self
  
class C_Name(ast.Name):
  def prepare(self):
    pass
  
  def print_c(self):
    if self.id == 'True':
      return 'true'
    elif self.id == 'False':
      return 'false'
    elif self.id == 'None':
      return '0'
    return self.id

if "NameConstant" in ast.__dict__:
  class C_NameConstant(ast.NameConstant):
    def prepare(self):
      pass
  
    def print_c(self):
      if self.value == True:
        # True
        return 'true'
      elif self.value == False:
        # False
        return 'false'
      else:
        return '0'
      
class C_Expr(ast.Expr):
  def prepare(self):
    pass
  
  def print_c(self):
    return self.value.print_c()

class C_UnaryOp(ast.UnaryOp):
  def prepare(self):
    pass
  
  def print_c(self):
    return self.op.print_c() + self.operand.print_c()
  
class C_UAdd(ast.UAdd):
  def prepare(self):
    pass
  
  def print_c(self):
    return '+'

class C_USub(ast.USub):
  def prepare(self):
    pass
  
  def print_c(self):
    return '-'

class C_Not(ast.Not):
  def prepare(self):
    pass
  
  def print_c(self):
    return '!'
    
class C_Invert(ast.Invert):
  def prepare(self):
    pass
  
  def print_c(self):
    return '~'

class C_BinOp(ast.BinOp):
  def prepare(self):
    pass
    
  def print_c(self):
    return '({left} {op} {right})'.format(
      left = self.left.print_c(),
      op = self.op.print_c(),
      right = self.right.print_c())
  

class C_Add(ast.Add):
  def prepare(self):
    pass
    
  def print_c(self):
    return '+'
  

class C_Sub(ast.Sub):
  def prepare(self):
    pass
    
  def print_c(self):
    return '-'
  

class C_Mult(ast.Mult):
  def prepare(self):
    pass
    
  def print_c(self):
    return '*'
  

class C_Div(ast.Div):
  def prepare(self):
    pass
    
  def print_c(self):
    return '/'
  

class C_Mod(ast.Mod):
  def prepare(self):
    pass
    
  def print_c(self):
    return '%'
  

class C_LShift(ast.LShift):
  def prepare(self):
    pass
    
  def print_c(self):
    return '<<'
  

class C_RShift(ast.RShift):
  def prepare(self):
    pass
    
  def print_c(self):
    return '>>'
  

class C_BitOr(ast.BitOr):
  def prepare(self):
    pass
    
  def print_c(self):
    return '|'
  

class C_BitXor(ast.BitXor):
  def prepare(self):
    pass
    
  def print_c(self):
    return '^'
  

class C_BitAnd(ast.BitAnd):
  def prepare(self):
    pass
    
  def print_c(self):
    return '&'
  

class C_BoolOp(ast.BoolOp):
  def prepare(self):
    pass
    
  def print_c(self):
    asC = '(' + self.values.pop(0).print_c()
    for value in self.values:
      asC += ' ' + self.op.print_c() + ' '
      asC += value.print_c()
    return asC + ')'
  

class C_And(ast.And):
  def prepare(self):
    pass
    
  def print_c(self):
    return '&&'
  

class C_Or(ast.Or):
  def prepare(self):
    pass
    
  def print_c(self):
    return '||'
  

class C_Compare(ast.Compare):
  def prepare(self):
    pass
    
  def print_c(self):
    asC = ''
    self.comparators.insert(0,self.left)
    addAnd = False
    for i,op in enumerate(self.ops):
      if addAnd:
        asC += ' && '
      else:
        addAnd = True
      asC += '(' + self.comparators[i].print_c() + ' '
      asC += op.print_c()
      asC += ' ' + self.comparators[i + 1].print_c() + ')'
    return asC
  

class C_Eq(ast.Eq):
  def prepare(self):
    pass
    
  def print_c(self):
    return '=='
  

class C_NotEq(ast.NotEq):
  def prepare(self):
    pass
    
  def print_c(self):
    return '!='
  

class C_Lt(ast.Lt):
  def prepare(self):
    pass
    
  def print_c(self):
    return '<'
  

class C_LtE(ast.LtE):
  def prepare(self):
    pass
    
  def print_c(self):
    return '<='
  

class C_Gt(ast.Gt):
  def prepare(self):
    pass
    
  def print_c(self):
    return '>'
  

class C_GtE(ast.GtE):
  def prepare(self):
    pass
    
  def print_c(self):
    return '>='
  

class C_Call(ast.Call):
  def prepare(self):
    pass
  
  def print_args(self):
    asC = ''
    for arg in self.args:
      asC += ', '
      asC += arg.print_c()
    return asC
    
  def print_c(self):
    if self.func.print_c() in renames:
      return module_rename(self)
    if isinstance(self.func,C_Attribute):
      # Convert OOP calls to regular function calls
      self.args.insert(0,self.func.value)
      self.func = C_Name(self.func.attr,None)
    asC = self.func.print_c() + '('
    useComma = False
    for arg in self.args:
      if useComma:
        asC += ', '
      else:
        useComma = True
      asC += arg.print_c()
    asC += ')'
    return asC
  

class C_IfExp(ast.IfExp):
  def prepare(self):
    pass
    
  def print_c(self):
    asC = '(' + self.test.print_c()
    asC += ' ? ' + self.body.print_c()
    asC += ' : ' + self.orelse.print_c() + ')'
    return asC
  

class C_Attribute(ast.Attribute):
  def prepare(self):
    pass
    
  def print_c(self):
    return self.value.print_c() + '.' + self.attr
  

class C_Subscript(ast.Subscript):
  def prepare(self):
    pass
    
  def print_c(self):
    return self.value.print_c() + '[' + self.slice.print_c() + ']'
  

class C_Index(ast.Index):
  def prepare(self):
    pass
    
  def print_c(self):
    return self.value.print_c()
  

class C_Assign(ast.Assign):
  def prepare(self):
    pass
    
  def print_c(self):
    asC = ''
    for target in self.targets:
      asC += target.print_c() + ' = '
    asC += self.value.print_c()
    return asC
  
if "AnnAssign" in ast.__dict__:
  class C_AnnAssign(ast.AnnAssign):
    def prepare(self):
      pass
    
    def print_c(self):
      asC = self.annotation.print_c() + ' '
      asC += self.target.print_c()
      if isinstance(self.value, C_Call) and self.value.func.print_c() in classNames:
        asC += ';\n'
        asC += self.value.func.print_c() + '___init__('
        asC += self.target.print_c()
        asC += self.value.print_args() + ')'
      else:
        if self.value:
          asC += ' = ' + self.value.print_c()
      return asC
  

class C_AugAssign(ast.AugAssign):
  def prepare(self):
    pass
    
  def print_c(self):
    asC = self.target.print_c() + ' '
    asC += self.op.print_c() + '= '
    asC += self.value.print_c()
    return asC
  

class C_Assert(ast.Assert):
  def prepare(self):
    pass
    
  def print_c(self):
    return 'VERIFY(' + self.test.print_c() + ')'
  

class C_Pass(ast.Pass):
  def prepare(self):
    pass
    
  def print_c(self):
    return ''
  

class C_Import(ast.Import):
  def prepare(self):
    pass
    
  def print_c(self):
    importName = '/'.join(self.names[0].name.split('.'))
    return '#include ' + importName + '.c\n'


class C_If(ast.If):
  def prepare(self):
    pass
    
  def print_c(self):
    asC = 'if ('
    asC += self.test.print_c()
    if sameLineBraces:
      asC += ') {\n'
    else:
      asC += ')\n{\n'
    for childNode in self.body:
      try:
        unindented = childNode.print_c()
        unindented = '\n'.join([indent + x for x in unindented.split('\n')])
        if not unindented.endswith('}'):
          unindented += ';'
        unindented += '\n'
        asC += unindented
      except Exception as e:
        print(traceback.format_exc())
        print(ast.dump(childNode))
        return asC
    asC += '}'
    if self.orelse:
      if sameLineBraces:
        asC += ' else {\n'
      else:
        asC += '\nelse\n{\n'
      for childNode in self.orelse:
        try:
          unindented = childNode.print_c()
          unindented = '\n'.join([indent + x for x in unindented.split('\n')])
          if not unindented.endswith('}'):
            unindented += ';'
          unindented += '\n'
          asC += unindented
        except Exception as e:
          print(traceback.format_exc())
          print(ast.dump(childNode))
          return asC
      asC += '}'
    return asC
  

class C_For(ast.For):
  def prepare(self):
    pass
    
  def print_c(self):
    # Only supports for _ in range() for now
    asC = ''
    var = self.target.print_c()
    low = '0'
    step = '1'
    if len(self.iter.args) > 1:
      low = self.iter.args[0].print_c()
      high = self.iter.args[1].print_c()
      if len(self.iter.args) > 2:
        step = self.iter.args[2].print_c()
    else:
      high = self.iter.args[0].print_c()
    asC += 'for (' + var + ' = '
    asC += low
    asC += '; ' + var + ' < ' + high + '; ' + var + ' += ' + step
    if sameLineBraces:
      asC += ') {\n'
    else:
      asC += ')\n{\n'
    for childNode in self.body:
      try:
        unindented = childNode.print_c()
        unindented = '\n'.join([indent + x for x in unindented.split('\n')])
        if not unindented.endswith('}'):
          unindented += ';'
          unindented += '\n'
          asC += unindented
      except Exception as e:
        print(traceback.format_exc())
        print(ast.dump(childNode))
        return asC
    return asC + '}'

class C_While(ast.While):
  def prepare(self):
    pass
    
  def print_c(self):
    asC = 'while (' + self.test.print_c()
    if sameLineBraces:
      asC += ') {\n'
    else:
      asC += ')\n{\n'
    for childNode in self.body:
      try:
        unindented = childNode.print_c()
        unindented = '\n'.join([indent + x for x in unindented.split('\n')])
        if not unindented.endswith('}'):
          unindented += ';'
          unindented += '\n'
          asC += unindented
      except Exception as e:
        print(traceback.format_exc())
        print(ast.dump(childNode))
        return asC
    return asC + '}'
  

class C_Break(ast.Break):
  def prepare(self):
    pass
    
  def print_c(self):
    return 'break'
  

class C_Continue(ast.Continue):
  def prepare(self):
    pass
    
  def print_c(self):
    return 'continue'

class C_Return(ast.Return):
  def prepare(self):
    pass
  
  def print_c(self):
    return 'return ' + self.value.print_c()

class C_ClassDef(ast.ClassDef):
  def prepare(self):
    classNames.append(self.name)
  
  def print_c(self):
    asC = '/*** Class: ' + self.name + ' ***/\n'
    varNames = ClassVariables.scanIn(self)
    if ast.get_docstring(self):
      asC += '/*\n'
      asC += ast.get_docstring(self)
      self.body.pop(0)
      asC += '\n*/\n'
    asC += 'typedef struct'
    if sameLineBraces:
      asC += ' {\n'
    else:
      asC += '\n{\n'
    for var,type in varNames.items():
      asC += indent + type + ' ' + var + ';\n'
    asC += '} ' + self.name + ';\n'
    for node in self.body:
      try:
        asC += node.print_c()
      except Exception as e:
        print(traceback.format_exc())
        print("Current code:")
        print(asC)
    asC += '\n/*** End Class: ' + self.name + ' ***/\n'
    return asC

class ClassVariables(ast.NodeVisitor):

  def __init__(self,*args,**kwargs):
    super(ClassVariables,self).__init__(*args,**kwargs)
    self.varNames = {}
  
  def visit_C_AnnAssign(self, aNode):
    if aNode.target.print_c().startswith('self.'):
      if aNode.target.attr in self.varNames:
        if not self.varNames[aNode.target.attr] == aNode.annotation.print_c():
          raise TypeError("Redefining a type not permitted in {}->{}".format(self.parentNode.name,aNode.target.print_c()))
      else:
        self.varNames[aNode.target.attr] = aNode.annotation.print_c()
        aNode.__class__ = C_Assign
        aNode.targets = [aNode.target]
    self.generic_visit(aNode)
  
  @classmethod
  def scanIn(cls, aNode):
    walker = cls()
    walker.parentNode = aNode
    walker.visit(aNode)
    return walker.varNames

class CNodeTransformer(ast.NodeVisitor):
  def __init__(self, *args, **kwargs):
    self.toPrepare = []
    self.currentClass = None
    super(CNodeTransformer,self).__init__(*args,**kwargs)
    
  def visit_C_Import(self, aNode):
    # Make sure that we've compiled this file.
    filePath = '/'.join(aNode.names[0].name.split('.')) + '.py'
    compile_to_c(filePath)

  def visit_C_ClassDef(self, aNode):
    previousClass = self.currentClass
    self.currentClass = aNode
    self.generic_visit(aNode)
    self.currentClass = previousClass
    
  def visit_C_FunctionDef(self, aNode):
    if self.currentClass:
    # Since we're scanning this anyways, get this function ready for a class!
      if aNode.name == '__init__':
        aNode.name = self.currentClass.name + '_' + aNode.name
      aNode.args.args[0].annotation = self.currentClass.name # Force use of class
    self.generic_visit(aNode)

  def visit(self, node):
    """Visit a node."""
    if 'C_' + node.__class__.__name__ in globals():
      node.__class__ = globals()['C_' + node.__class__.__name__]
      self.toPrepare.append(node)
    method = 'visit_' + node.__class__.__name__
    visitor = getattr(self, method, self.generic_visit)
    visitor(node) # Recursively replace classes

def compile_to_c(filename):
  if not os.path.exists(filename):
    if os.path.exists(os.path.join(os.path.dirname(os.path.realpath(__file__)),filename)):
      filename = os.path.join(os.path.dirname(os.path.realpath(__file__)),filename)
    else:
      if os.path.exists(os.path.join(os.path.dirname(os.path.realpath(sys.argv[1])),filename)):
        filename = os.path.join(os.path.dirname(os.path.realpath(sys.argv[1])),filename)
      else:
        raise FileNotFoundError(filename)
  if not os.path.abspath(filename) in compiled:
    module = ast.parse(open(filename, 'r').read())
    compiled[os.path.abspath(filename)] = '' # At least fill it in
    transformer = CNodeTransformer()
    transformer.visit(module)
    for nodeToPrepare in transformer.toPrepare:
      nodeToPrepare.prepare()
    compiled[os.path.abspath(filename)] = module.print_c()

def commonprefix(l):
  # this unlike the os.path.commonprefix version
  # always returns path prefixes as it compares
  # path component wise
  cp = []
  ls = [p.split(os.path.sep) for p in l]
  ml = min( len(p) for p in ls )
  for i in range(ml):
    s = set( p[i] for p in ls )         
    if len(s) != 1:
        break
    cp.append(s.pop())
  return os.path.sep.join(cp)

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print(f"Usage: {__file__} [file]")
    sys.exit(1)
  compile_to_c(sys.argv[1])
  common = commonprefix(compiled)
  withRelNames = {os.path.relpath(abspath,common):contents for abspath,contents in compiled.items()}
  for file,contents in withRelNames.items():
    filename = os.path.join(os.path.dirname(os.path.realpath(sys.argv[1])),os.path.join('output',os.path.splitext(file)[0] + '.c'))
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename,'w') as c_file:
      c_file.write(contents)
