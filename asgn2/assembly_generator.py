import register_allocator
import data
from data import debug

def boilerplate() :
    '''Generates Variable space and other directives. '''
    print(".section .data")
    for v in data.vset:
        print("{}:".format(v))
        print("\t.long {}".format(1))
    print("\n.section .text\n")
    print('\nprintFormat:  .asciz "%d\\n"')
    print('\nscanFormat:  .asciz "%d"\n')
    print('.global main\n')
    print('main:')
    pass


def programEnd():
    print("\tmovl $1, %eax\n\tmovl $0, %ebx\n\tint $0x80")


def assembly_generator() :
    '''Entry point for assembly generation after parse_il()'''
    def block_assembly_generator() :
        '''Generates assembly code for current block. '''
        data.numins = len(data.block)
        register_allocator.initblock()
        for i in range(0, len(data.block) - 1):
            register_allocator.ini()
            OP_MAP[data.block[i].type](i)
        i = len(data.block) - 1
        if data.block[i].type in {'call', 'ret', 'goto'}:
            register_allocator.save_to_memory()
            register_allocator.ini()
            OP_MAP[data.block[i].type](i)
        else :
            register_allocator.ini()
            OP_MAP[data.block[i].type](i)
            register_allocator.save_to_memory()
        for line in data.out :
            print ("\t" + line)

    boilerplate()
    breakpoints = set()
    breakpoints.add(0)
    for i in range(0,len(data.raw)) :
        if data.raw[i].type == 'label' :
            breakpoints.add(i)
        if data.raw[i].type == 'goto' :
            breakpoints.add(i+1)
            # breakpoints.add(int(data.raw[i].out)-1)
        if data.raw[i].type == 'call' :
            breakpoints.add(i+1)
        if data.raw[i].type == 'ret' :
            breakpoints.add(i + 1)
    breakpoints.add(len(data.raw))
    breakpoints = sorted(breakpoints)
    for i in range(0,len(breakpoints)-1) :
        data.out.clear()
        if data.raw[breakpoints[i]].type == 'label' :
            print("\n{}:".format(data.raw[breakpoints[i]].out))
        if i==0:
           data.block = data.raw[breakpoints[i]:breakpoints[i+1]]
        else:
           data.block = data.raw[breakpoints[i] + 1:breakpoints[i+1]]
        block_assembly_generator()
    # programEnd()


###  OP_CODE SRC, DEST

def ADD(i) :
    (x, y, z) = (data.block[i].out, data.block[i].in1, data.block[i].in2)
    try :
        int(z)
        data.zprime = z
    except :
        register_allocator.getz(z)
        pass
    register_allocator.getreg(x, y, i)
    try :
        int(y)
        data.yprime = y
    except :
        pass
    register_allocator.gety(y)
    data.out.append("addl " + register_allocator.transform(data.zprime) + ", " + register_allocator.transform(data.L))
    register_allocator.update(x)
    register_allocator.freereg(y, i)
    register_allocator.freereg(z, i)

def SUB(i) :
    (x, y, z) = (data.block[i].out, data.block[i].in1, data.block[i].in2)
    try :
        int(z)
        data.zprime = z
    except :
        register_allocator.getz(z)
        pass
    register_allocator.getreg(x, y, i)
    try :
        int(y)
        data.yprime = y
    except :
        pass
    register_allocator.gety(y)
    data.out.append("subl " + register_allocator.transform(data.zprime) + ", " + register_allocator.transform(data.L))
    register_allocator.update(x)
    register_allocator.freereg(y, i)
    register_allocator.freereg(z, i)

def MUL(i) :
    (x, y, z) = (data.block[i].out, data.block[i].in1, data.block[i].in2)
    try :
        int(z)
        data.zprime = z
    except :
        register_allocator.getz(z)
        pass
    register_allocator.getreg(x, y, i)
    try :
        int(y)
        data.yprime = y
    except :
        pass
    register_allocator.gety(y)
    data.out.append("imul " + register_allocator.transform(data.zprime) + ", " + register_allocator.transform(data.L))
    register_allocator.update(x)
    register_allocator.freereg(y, i)
    register_allocator.freereg(z, i)

def ASSIGN(i) :
    (x, y) = (data.block[i].out, data.block[i].in1)
    register_allocator.getreg(x, y, i)
    try :
        int(y)
        data.yprime = y
    except :
        pass
    register_allocator.gety(y)
    register_allocator.update(x)
    register_allocator.freereg(y, i)

def DIV(i) :
    (x, y, z) = (data.block[i].out, data.block[i].in1, data.block[i].in2)
    register_allocator.push('edx')
    data.out.append("xor %edx, %edx")
    try :
        int(z)
        reg = register_allocator.empty_reg(['edx', 'eax'], i)
        data.out.append('mov $' + z + ", %" + reg)
        data.zprime = reg
    except :
        if data.adesc[z] == 'eax':
            register_allocator.push(z)
        register_allocator.getz(z)
        pass
    register_allocator.getreg(x, y, i, 'eax')
    try :
        int(y)
        data.yprime = y
    except :
        pass
    register_allocator.gety(y)
    data.out.append("idivl " + register_allocator.transform(data.zprime))
    register_allocator.update(x)
    register_allocator.freereg(y, i)
    register_allocator.freereg(z, i)

def MOD(i):
    (x, y, z) = (data.block[i].out, data.block[i].in1, data.block[i].in2)
    register_allocator.push('edx')
    data.out.append("xor %edx, %edx")
    try :
        int(z)
        data.zprime = z
        reg = register_allocator.empty_reg(['eax', 'edx'], i)
        data.out.append('mov $' + z + ", %" + reg)
        data.zprime = reg

    except :
        if data.adesc[z] == 'eax':
            register_allocator.push(z)
        register_allocator.getz(z)
        pass
    register_allocator.getreg(x, y, i, 'eax')
    try :
        int(y)
        data.yprime = y
    except :
        pass
    register_allocator.gety(y)
    data.out.append("idivl " + register_allocator.transform(data.zprime))
    data.L = 'edx'
    register_allocator.update(x)
    register_allocator.freereg(y, i)
    register_allocator.freereg(z, i)

def AND(i):
    (x, y, z) = (data.block[i].out, data.block[i].in1, data.block[i].in2)
    try :
        int(z)
        data.zprime = z
    except :
        register_allocator.getz(z)
        pass
    register_allocator.getreg(x, y, i)
    try :
        int(y)
        data.yprime = y
    except :
        pass
    register_allocator.gety(y)
    data.out.append("and " + register_allocator.transform(data.zprime) + ", " + register_allocator.transform(data.L))
    register_allocator.update(x)
    register_allocator.freereg(y, i)
    register_allocator.freereg(z, i)

def OR(i):
    (x, y, z) = (data.block[i].out, data.block[i].in1, data.block[i].in2)
    try :
        int(z)
        data.zprime = z
    except :
        register_allocator.getz(z)
        pass
    register_allocator.getreg(x, y, i)
    try :
        int(y)
        data.yprime = y
    except :
        pass
    register_allocator.gety(y)
    data.out.append("or " + register_allocator.transform(data.zprime) + ", " + register_allocator.transform(data.L))
    register_allocator.update(x)
    register_allocator.freereg(y, i)
    register_allocator.freereg(z, i)

def XOR(i):
    (x, y, z) = (data.block[i].out, data.block[i].in1, data.block[i].in2)
    try :
        int(z)
        data.zprime = z
    except :
        register_allocator.getz(z)
        pass
    register_allocator.getreg(x, y, i)
    try :
        int(y)
        data.yprime = y
    except :
        pass
    register_allocator.gety(y)
    data.out.append("xor " + register_allocator.transform(data.zprime) + ", " + register_allocator.transform(data.L))
    register_allocator.update(x)
    register_allocator.freereg(y, i)
    register_allocator.freereg(z, i)

def RETURN(i) :
    data.out.append('ret')
    data.out.append('\n')

def CALL(i) :
    data.out.append('call ' + data.block[i].out)
    data.out.append('\n')


def PRINT(i):
    x = data.block[i].out
    try :
        data.adesc[x]
        data.out.append('pushl %' + data.adesc[x])
    except:
        data.out.append('pushl ' + x)
    data.out.append('pushl $printFormat')
    register_allocator.save_to_memory()
    data.out.append('call printf')
    data.out.append('addl $8, %esp')

def READ(i):
    x = data.block[i].out
    data.out.append('pushl $' + x)
    data.out.append('pushl $scanFormat')
    register_allocator.save_to_memory()
    data.out.append('call scanf')
    data.out.append('addl $8, %esp')

def GOTO(i):
    data.out.append('jmp ' + data.block[i].out)

OP_MAP = {'+': ADD, '-': SUB, '*': MUL, '=' : ASSIGN,'/' : DIV, '%' : MOD, '^' : XOR, '&' : AND, '|' : OR, 'ret' : RETURN, 'call' : CALL, 'print' : PRINT, 'read' : READ, 'goto' : GOTO}
