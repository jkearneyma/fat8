#! /usr/bin/python3

"""
"""

import sys, tty, termios, argparse
from intelhex import IntelHex

parser = argparse.ArgumentParser(
    description='fat8 emulator',
    epilog='')
parser.add_argument('ihex_file', type=str, help='Intel Hex file')
args = parser.parse_args()

mem = IntelHex(args.ihex_file)
PC = 0
insn = 0
reg = [0]*8 # A,B,C,D,E,H,L,M
flag = [False]*4 # carry,zero,sign,parity
stack = []
write_en = 0 # bit per 2KB block

# terminal I/O setup for fat8
# intercept calls to read/write character
def rst_handler(adr):
    global reg
    # handle character print specially
    if adr == 0o030:
        print(f'{chr(reg[0])}',end='',flush=True)
        reg[1] = 0o222 # B trashed
        return True
    # handle character input specially
    if adr == 0o040:
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            tty.setraw(fd)
            reg[0] = ord(sys.stdin.read(1))
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        if reg[0] == 0x03:
            dumpreg("Ctrl-C")
            exit(2)
        reg[1] = 0o222 # B trashed
        return True
    return False

def inp_handler(port):
    global write_en
    if port == 1:
        return write_en;
    print(f"(input {port:o})", end='')
    return 0;

def out_handler(port, value):
    global write_en
    if port == 1:
        write_en = value
    print(f"(output 1{port:o} {value:03o})", end='')

def write_handler(addr, value):
    global mem, write_en
    if ((write_en >> (addr / 0o4000)) & 1) == 0:
        print(f"(write violation {addr:05o} {value:03o})")
    else:
        mem[addr] = (value & 0o377)

def getreg(r):
    global mem, reg
    if (r==7):
        return mem[(reg[5] << 8) + reg[6]]
    else:
        return reg[r]

def dumpreg(msg = ''):
    global PC, insn, flag, stack
    print(f"\r\n{msg} PC {PC:05o} {insn:03o}  A {getreg(0):03o} B {getreg(1):03o} C {getreg(2):03o} D {getreg(3):03o} E {getreg(4):03o} H {getreg(5):03o} L {getreg(6):03o} M {getreg(7):03o}",'c' if flag[0] else 'nc', 'z' if flag[1] else 'nz', 's' if flag[2] else 'ns', 'p' if flag[3] else 'np')
    print('STACK: ',end='')
    print(' '.join(f'{s:05o}' for s in stack))

def setreg(r,value):
    global mem, reg
    if (r==7):
        write_handler((reg[5] << 8) + reg[6], value & 0o377)
    else:
        reg[r] = (value & 0o377)

def setfreg(r, value, setcarry = True):
    global mem, reg
    if setcarry: flag[0] = (value & 0o400) != 0
    flag[1] = ((value & 0o377) == 0o000)
    flag[2] = (value & 0o200) != 0
    flag[3] = ((value & 0o377).bit_count() & 1) == 0
    setreg(r, value)

def jmpto(to_adr):
    global PC
    if not rst_handler(to_adr):
        PC = to_adr

def callto(from_adr, to_adr):
    global stack, PC
    # this isn't actually a hardware error, but might catch
    # a software bug
    if len(stack) == 14:
        raise Exception("stack overflow")
    if not rst_handler(to_adr):
        stack.append(from_adr)
        PC = to_adr

def returnfrom():
    global stack, PC
    if len(stack) == 0:
        raise Exception("stack underflow")
    PC = stack.pop()

# execute one instruction
def step():
    global PC, mem, reg, flag, insn
    insn = mem[PC]
    PC += 1
    ddd = (insn & 0o070) >> 3
    sss = (insn & 0o007)
    match (0o300 & insn):
        case 0o000:
            match sss:
                case 0:
                    if ddd==0:
                        dumpreg("HLT/0")
                        exit()
                    setfreg(ddd, getreg(ddd)+1, False) # INd
                case 1:
                    if ddd==0:
                        dumpreg("HLT/1")
                        exit()
                    setfreg(ddd, getreg(ddd)-1, False) # DCd
                case 2:
                    match ddd:
                        case 0: # RLC
                            flag[0] = (reg[0] & 0o200) != 0
                            reg[0] = ((reg[0] << 1) & 0o377) + (1 if flag[0] else 0)
                        case 1: # RRC
                            flag[0] = (reg[0] & 0o001) != 0
                            reg[0] = ((reg[0] >> 1) & 0o177) + (0o200 if flag[0] else 0)
                        case 2: # RAL
                            reg[0] = ((reg[0] << 1) & 0o776) + (1 if flag[0] else 0);
                            flag[0] = (reg[0] & 0o400) != 0
                            reg[0] = (reg[0] & 0o377)
                        case 3: # RAR
                            nextcarry = (reg[0] & 1) != 0
                            reg[0] = ((reg[0] >> 1) & 0o177) + (0o200 if flag[0] else 0);
                            flag[0] = nextcarry
                        case _:
                            raise Exception(f"unhandled opcode 0o{insn:03o}")
                case 3: # RTc/RFc
                    if ((ddd & 0o4) != 0) == flag[ddd & 0o3]:
                        returnfrom()
                case 4:
                    match ddd:
                        case 0: # ADI
                            setfreg(0, reg[0] + mem[PC])
                        case 1: # ACI
                            setfreg(0, reg[0] + mem[PC] + (1 if flag[0] else 0))
                        case 2: # SUI
                            setfreg(0, reg[0] - mem[PC])
                        case 3: # SBI
                            setfreg(0, reg[0] - mem[PC] - (1 if flag[0] else 0))
                        case 4: # NDI
                            setfreg(0, reg[0] & mem[PC])
                        case 5: # XRI
                            setfreg(0, reg[0] ^ mem[PC])
                        case 6: # ORI
                            setfreg(0, reg[0] | mem[PC])
                        case 7: # CPI
                            save = reg[0]
                            setfreg(0, reg[0] - mem[PC])
                            reg[0] = save
                        case _:
                            raise Exception(f"unhandled opcode 0o{insn:03o}")
                    PC += 1
                case 5: # RST d
                    callto(PC, ddd << 3)
                case 6: # LdI
                    setreg(ddd, mem[PC])
                    PC += 1
                case 7:
                    returnfrom()
                case _:
                    raise Exception(f"unhandled opcode 0o{insn:03o}")
        case 0o100:
            match sss:
                case 0: # JFc/JTc
                    if ((ddd & 0o4) != 0) == flag[ddd & 0o3]:
                        PC = mem[PC] + ((mem[PC + 1] & 0o077) << 8)
                    else:
                        PC += 2
                case 2: # CFc/CTc
                    if ((ddd & 0o4) != 0) == flag[ddd & 0o3]:
                        callto(PC + 2, mem[PC] + ((mem[PC + 1] & 0o077) << 8))
                    else:
                        PC += 2
                case 4: # JMP
                    jmpto(mem[PC] + ((mem[PC + 1] & 0o077) << 8))
                case 6: # CAL
                    callto(PC + 2, mem[PC] + ((mem[PC + 1] & 0o077) << 8))
                case _:
                    if (insn & 1) != 0:
                        # IO
                        if (insn & 0o060) != 0:
                            out_handler((insn & 0o016)>>1, reg[0])
                        else:
                            reg[0] = inp_handler((insn & 0o016)>>1)
                    else:
                        raise Exception(f"unhandled opcode 0o{insn:03o}")
        case 0o200:
            match ddd:
                case 0: # ADs
                    setfreg(0, reg[0] + getreg(sss))
                case 1: # ACs
                    setfreg(0, reg[0] + getreg(sss) + (1 if flag[0] else 0))
                case 2: # SUs
                    setfreg(0, reg[0] - getreg(sss))
                case 3: # SBs
                    setfreg(0, reg[0] - getreg(sss) - (1 if flag[0] else 0))
                case 4: # NDs
                    setfreg(0, reg[0] & getreg(sss))
                case 5: # XRs
                    setfreg(0, reg[0] ^ getreg(sss))
                case 6: # ORs
                    setfreg(0, reg[0] | getreg(sss))
                case 7: # CPs
                    save = reg[0]
                    setfreg(0, reg[0] - getreg(sss))
                    reg[0] = save
                case _:
                    raise Exception(f"unhandled opcode 0o{insn:03o}")
        case 0o300:
            # all ones is a HLT because LMM makes no sense
            if insn == 0o377:
                dumpreg("HLT/7")
                exit()
            # 'lxy' where x==y and x>0 cause a register print for debugging
            if sss >  0 and sss == ddd:
                dumpreg('debug' + str(sss))
            setreg(ddd, getreg(sss))
        case _:
            raise Exception(f"unhandled opcode 0o{insn:03o}")

try:
    while True:
        step()
except Exception as e:
    print('\r\n',e)
    dumpreg('registers')

