#===========================================================================================================#
# Name  : MIPSAssembler.py
# Author: T.K.R.Arvind
# Date  : 6th Jan 2021
# 
# This program takes in assembly program written @INPATH checks for errors and converts to MIPS
# HEX and (R/J/I type formatted) binary codes @OUTPUT.
#
# HIGHLIGHTS:
#          1) It understands "goto TAGS" e.g j START
#          2) It detects and points error and the line as well as the possible errors
#          3) It interprets any name to register file whether it precedes with $ or not e.g $s1 or s1
#          4) It is customisable to machine dependent opcode and function values by changing in 'MNEMONICSPATH'
#          5) It interprets $a as registers e.g $1 -> $r1 while just 1 doesnot refer to any register
#          6) It can adopt to variable register file width say 64/128 by changing Values in 'constant used'
#
# NOTE: This program needs two dictionaries. One for register names and other having pnemonics to opcode 
#============================================================================================================# 

import sys

#============================================================================================================# 
#                                           PATH Variables
#============================================================================================================#
INPATH = "./test/input.txt"                #Path where the input assembly program is written
OUTPUT = "./test/machineCodeOutput.txt"    #Path where the output program is generated

TMP = "assembler.tmp"               #run time generated temp file
MNEMINOCSPATH = "mnemonics.dict"    #reference file for assembler
REGNAMES = "regNames.dict"          #reference file for assembler

#============================================================================================================# 
#                                           Constants Used
#============================================================================================================# 
REGFILESIZE = 32             #Number of register available 32
REGBITWIDTH = 5              #Rs,Rt,Rd,SA are represented by 5 bits/can be changed if needed
FUNCTIONBITWIDTH = 6         #Function is represented with 6 bits
OFFSETBITWIDTH = 16          #Offset/Immediate is 16 bits
TARGETBITWIDTH = 26          #target in 'j target' is represented with 26 bits



#============================================================================================================# 
#                                       Global Variable Used
#============================================================================================================# 
MemDictionary = {"root":0}   #Holds the memory location of TAGS and root represents the start of the memory program
PNUMANICSdictionary = {}     #Holds the pnemonics to opcode conversion description
RegNameDictionary = {}       #Holds the names of registers
WarningFlag = False
WarningCount = 0             #Counter for the warning produced

#=============================================================================================================#
#               Reads the opcode dictionary which is used as reference table for conversion
#=============================================================================================================#
try:
    opcodefile = open(MNEMINOCSPATH,'r')
    for dline in iter(lambda: opcodefile.readline(), ''):               #iterating throughout the file till EOF
        dline = dline.split("\n")[0].split("\r")[0].split("#")[0]       #extrating key values from eol and other extras
        if not dline:
            continue
        dlist = dline.split()                                           #spliting the words in each line as list
        PNUMANICSdictionary[dlist[0]] = dlist[1:]
except IOError:
    print("ERROR: "+str(MNEMINOCSPATH)+"file not found in the directory"+"\nTerminating the program.....")
    sys.exit(1)
     
#=============================================================================================================#
#                   Reads the register names used as reference table for conversion
#=============================================================================================================#
try:
    regnames = open(REGNAMES,'r')
    for dline in iter(lambda: regnames.readline(), ''):                 #iterating throughout the file till EOF
        dline = dline.split("\n")[0].split("\r")[0]                     #extrating key values from eol and other extras
        if not dline:
            continue
        [key,value] = dline.split()                                     #spliting the words in each line as list
        RegNameDictionary[key] = value
except IOError:
    print("ERROR: "+str(REGNAMES)+" file not found in the directory"+"\nTerminating the program.....")
    sys.exit(1)


#========================================== Register Value Finder =============================================#
#   This function takes in the key value to be searched in the RegNameDictionary. It also converts any upper case
#   char to lowercase  as dictionary contains only lower case. It returns interger value representing the register 
#   or the 'immediate' value in the asm code
#=============================================================================================================#
def registerValue(value,asm,LineNumber):
    global WarningFlag 
    keyCaps = ''
    valuepair = ''
    parsedvalue = value.lower().split()[0]    
    dollarRemoved = parsedvalue.split('$') 
    
    if(dollarRemoved[0] == '' or dollarRemoved[0] == ' ' ):             #if value is wit $ i.e $20 = ['','20'
        keyCaps = dollarRemoved[1]
    else:
        keyCaps = dollarRemoved[0]                                      #if value is without $ i.e 20 = ['20']

    numberCount = 0                                                     #checking number of numeral value
    keyLength = len(keyCaps)
    keyformatted = ''
    
    for i in range(0,keyLength):
        if(keyCaps[i] >= '0' and keyCaps[i] <= '9'):                    #if numbers  
            keyformatted += keyCaps[i]
            numberCount +=  1
        elif((keyCaps[i] >= 'a' and keyCaps[i] <= 'z') or (keyCaps[i] >= 'A' and keyCaps[i] <= 'Z')):#if alphabets convert to lower case
            keyformatted += keyCaps[i].lower()
        elif(keyCaps[i] == '-' or keyCaps[i] == '+'):
            keyformatted += keyCaps[i]
            numberCount +=  1
        else:                                                           #else print error
            print("WARNING in line "+str(LineNumber)+": asm has some unusual character '"+keyCaps[i]+"' in value "+value+" at asm -"+asm)
            WarningFlag = True
            return int(0)
            
    if(numberCount == keyLength):                                       #if string has only numbers
        return int(keyformatted)
    
    try:
        valuepair = RegNameDictionary[keyformatted]                     #check is the register name is avaialble in dictionary
    except KeyError:
        print("WARNING in line "+str(LineNumber)+": Value "+keyformatted+" is neither a number nor represent any register in line -"+asm)
        WarningFlag = True
        return int(0)
        
    return int(valuepair)   
#==================================================================================================================#







#==================================================================================================================#
#   This function takes in the offset value and if it  is negative then it converts to its equivalent 
#   unsigned positive number of given max bits. If positive number cannot be represented within the given
#   max bits it is catched in code  
#==================================================================================================================#
def NegToPosINT(value,Nbits,LineNumber,shouldBePositive = False):
    global WarningFlag 
    if(value <0 ):
        if(shouldBePositive):                                           #for value constrained to be positive
            print("WARNING in line "+str(LineNumber)+": offset "+str(value)+" cannot be negative ")
            WarningFlag = True
            value = 0
        elif ((-1*value) > 2**(Nbits - 1)) :                            #max negative value should be 2**(Nbits-1)
            print("WARNING in line "+str(LineNumber)+": Value "+str(value)+" exceeds allowed offset bit "+str(Nbits))
            WarningFlag = True
            value = 0                                                   #for 3bit max neg is -4, if -20 is given it returns 0
        else:
            value = value + (1<<Nbits)                                  #(-1) = 2^Nbits-1, (-2)= 2^Nbits-2...
    elif (value >= 2**(Nbits - 1)):                                     #Max positive value is 2**(Nbits-1)-1
            print("WARNING in line "+str(LineNumber)+": Value "+str(value)+" exceeds allowed offset bit "+str(Nbits))
            WarningFlag = True
            value = 0                                                   #for 3bit max pos is 3, if 5 is given it returns 0
    return value
#==================================================================================================================#







#======================================== Offset Calculator =======================================================#
#   This Function takes in offset value which can be integer directly or tag. If the tag is found in
#   dictionary then it wil calculate the relative position. If it is jump it calculates the absolute
#   position in the memory. if not it will raise error flag. 
#==================================================================================================================#
def OffsetCalculator(value,CurrentMem,asm,LineNumber,isjump = False):
    tmpb = 0
    global WarningFlag
    try:                                    #trying to see whether it is given as 'int' offset
        tmpb =  int(value)
    except ValueError:                      #if it is a tag
        tmp = value.split()                 #if it is a invalid tag woth spaces
        if(len(tmp)>1):
            print("WARNING in line "+str(LineNumber)+": TAG "+  value +" has space inside, in asm -"+asm)
            WarningFlag = True
        key = tmp[0]                        # it has only key
        if key in MemDictionary:            #if the key is found find the relative position
            if(isjump):                     #If jump instruction
                tmpb = (int(MemDictionary[key]))
            else:                           #relative position
                tmpb = (int(MemDictionary[key]) - CurrentMem - 1) 
        else:                               #else store the position to which it will be updated later
            WarningFlag = True
            print("WARNING in line "+str(LineNumber)+": @"+  value +" is not found in the program")
    return tmpb
#==================================================================================================================#






#===================================== Assembly To Machine Code Converter =========================================#
#   This function takes in asm without any comments or tags converts to assembly program using
#   dictionary from .PNUMANICSdictionary.txt file and returns the machine code or ERROR
#==================================================================================================================#
def assemblyConverter(asm,CurrentMem,LineNumber): 
    global WarningFlag 
    WarningFlag = False
    #--------------------------------------Example ------------------------------------------------#
    #   input : addi $s1,$s2 , 100
    #   pnewmatics : addi
    #   commasep : ['addi $s1', '$s2' , '100']
    #   values   : ['addi','$s1','$s2','100']
    # ---------------------------------------------------------------------------------------------#
    Mnemonics = asm.split()[0].lower()            #seperating the Mnemonics and values 
    if(Mnemonics == 'nop'):                       #only for 'nop' special case there are no target/register 
        return '0'* REGFILESIZE
    commasep = asm.split(',') 
    listLength = len(commasep)
    
    #-------------- what if the input is done without comma e.g. addi $s1 $s2, 100-----------------#
    #   commasep = ['addi $s1 $s2','100']
    #   commasep[0].split() = ['addi','$s1','$s2']
    #-----------------------------------------------------------------------------------------------#
    if(len(commasep[0].split()) != 2 ):
        print("WARNING in line "+str(LineNumber)+": Missing values or a comma between $registers in asm -"+asm)
        return "WARNING"
        
    values = [Mnemonics, commasep[0].split()[1]]
    if(listLength > 1):
        values.extend(commasep[1:])
        
    #-------------- what is the input is done without comma e.g. addi  $s1 , $s2 100-----------------#
    #   values = ['addi',' $1','$s2 100']
    #   values[0].split()  = ['addi']
    #   values[1].split() = ['$s1']
    #   values[2].split() = ['$s2','100'] catches these error
    #   and removes extra spaces infront or back of say $s1 
    #----------------------------------------------------------------------------------------------#
    
    for i in range(0,len(values)):       
        valueSplitter = values[i].split()
        
        if(len(valueSplitter) > 1):
            print("WARNING in line "+str(LineNumber)+": '"+ str(values[i])+"' has a comma or paranthesis missing in asm -"+asm)
            return "WARNING"
        else:
            values[i] = valueSplitter[0]
  
    if Mnemonics not in PNUMANICSdictionary:
        print("WARNING in line "+str(LineNumber)+": {"+str(Mnemonics)+"} in the asm ="+str(asm)+"= is not  found in dictionary, you can update in 'PNUMANICS.dict'")
        return "WARNING"
    
    #----------------------------------------------------------------------------------------------#
    # bringing in the description as list for the Mnemonics from PNUMANICSdictionary
    # descriptionMnemonics contains 1)no. of param required 2)hasValue 3)opcode 4) function(optional)  
    # hasValue indiates whether it is a 1)arithmetic 2)branch 3)shiftt 4)jump 5)memory operation
    #----------------------------------------------------------------------------------------------#
    descriptionMnemonics = PNUMANICSdictionary[Mnemonics] 
    paramRequired = descriptionMnemonics[0]
    hasValue = descriptionMnemonics[1]   
    opcode = descriptionMnemonics[2]
     
    a = 0  #for holding the $values
    b = 0  #for holding the $values
    c = 0  #for holding the $values
    
    machineCode = opcode+'_' 
   
    
    
    #--------------------------------------- For the asm that requires three register values -------------------------#
    if(int(paramRequired) == 3):
        if(len(values) != 4):
           print("WARNING in line "+str(LineNumber)+": "+str(asm)+" is missing a parameters")
           return "WARNING"
        a =  registerValue(values[1],asm,LineNumber)  
        b =  registerValue(values[2],asm,LineNumber)  
        c =  registerValue(values[3],asm,LineNumber)  
        
        if(WarningFlag):
            return "WARNING"
            
        if(a > REGFILESIZE or b > REGFILESIZE or c > REGFILESIZE):             #if the value goes more than allowed bitsize 
            print("WARNING in line "+str(LineNumber)+": Register value greater than "+ str(REGFILESIZE)+" is not accepted -"+asm)
            return "WARNING"
            
        if(a == 0):
            print("WARNING in line "+str(LineNumber)+": Zero Register cannot be assigned -"+asm)
            return "WARNING"
            
        if(hasValue == 'a'):                    #add rd, rs, rt
            machineCode += bin(b).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #rs
            machineCode += bin(c).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #rt 
            machineCode += bin(a).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #rd
            machineCode += bin(0).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #sa
        elif(hasValue == 's'):                  #sll rd, rt, sa
            if(c<0):
               print("WARNING in line "+str(LineNumber)+": Shift value should be positive -"+asm)
               return "WARNING" 
            machineCode += bin(0).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #rs
            machineCode += bin(b).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #rt
            machineCode += bin(a).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #rd
            machineCode += bin(c).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #sa
        else:                                   #sllv rd, rt, rs
            machineCode += bin(c).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #rs
            machineCode += bin(b).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #rt
            machineCode += bin(a).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #rd
            machineCode += bin(0).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'    #sa
            
        machineCode += descriptionMnemonics[3]
            
    #--------------------------------------- For the asm that requires two register values -------------------------#        
    elif(int(paramRequired) == 2):  
        
        #---------------------------------------------- immediate arguments ------------------------------------#
        if(hasValue == 'a'):                    #addi rt,rs,immediate 
            if(len(values) != 4):
                print("WARNING in line "+str(LineNumber)+": -"+str(asm)+"-  is missing a parameters")
                return "WARNING"
            a =  registerValue(values[2],asm,LineNumber)  #rs
            b =  registerValue(values[1],asm,LineNumber)  #rt
            c =  NegToPosINT(registerValue(values[3],asm,LineNumber),OFFSETBITWIDTH,LineNumber)  #---> signed
            
        #----------------------------------------------- branches ---------------------------------------------#
        elif(hasValue == 'b'):                  #bne rs,rt,offset
            if(len(values) != 4):
                print("WARNING in line "+str(LineNumber)+": -"+str(asm)+"-  is missing a parameters")
                return "WARNING"
            a =  registerValue(values[1],asm,LineNumber) #rs
            b =  registerValue(values[2],asm,LineNumber) #rt
            tmpc= OffsetCalculator(values[3],CurrentMem,asm,LineNumber)       #offset: either Value/Tag can be present
            c = NegToPosINT(tmpc,OFFSETBITWIDTH,LineNumber)                   #converting offset value to "unsigned integer"  
         
        #----------------------------------------------- memory ---------------------------------------------#
        else:                                   #lw rt, offset(rs)
            if(len(values) != 3):
                print("WARNING in line "+str(LineNumber)+": -"+str(asm)+"- is missing a parameters or paranthesis")
                return "WARNING"
             
            b =  registerValue(values[1],asm,LineNumber)   #rt
            if(values[2].find('(') > 0 and values[2].find(')') > 0):
                a =  registerValue(values[2].split(')')[0].split('(')[1],asm,LineNumber) #rs
                tmpc = OffsetCalculator(values[2].split(')')[0].split('(')[0],CurrentMem,asm,LineNumber) #offset: either Value/Tag can be present
                c = NegToPosINT(tmpc,OFFSETBITWIDTH,LineNumber)               #converting offset value to "unsigned integer" 
            else:
                print("WARNING in line "+str(LineNumber)+": -"+str(asm)+"- is missing parameters or paranthesis")
                return "WARNING"

        #(a = rs b = rt  c = imm/off)
        if(WarningFlag):
            return "WARNING"
            
        if( b == 0 and (hasValue == 'a' or hasValue == 'ml')): #immediate and load Mnemonics should not assign zero register 
            print("WARNING in line "+str(LineNumber)+": Zero Register cannot be assigned -"+asm)
            return "WARNING"
                
        if(a > REGFILESIZE or b > REGFILESIZE ):                            #if the value goes more than allowed bitsize 
            print("WARNING in line "+str(LineNumber)+": Register value greater than "+ str(REGFILESIZE)+" is not accepted - "+asm)
            return "WARNING"
        machineCode += bin(a).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'     #rs
        machineCode += bin(b).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'     #rt
        machineCode += bin(c).split('0b')[1].rjust(OFFSETBITWIDTH,'0')      #immediate /offset
    
    #--------------------------------------- For the asm that requires one register values -------------------------# 
    elif(int(paramRequired) == 1): 
    
        #----------------------------------------------- branch ---------------------------------------------#
        if(hasValue == 'b'):                #bgez rs, offset
            if(len(values) != 3):
               print("WARNING in line "+str(LineNumber)+": -"+str(asm)+"- is missing some parameters")
               return "WARNING"
            a =  registerValue(values[1],asm,LineNumber)
            tmpb = OffsetCalculator(values[2],CurrentMem,asm,LineNumber)    #offset: either Value/Tag can be present
            b = NegToPosINT(tmpb,OFFSETBITWIDTH,LineNumber)                 #converting offset value to "unsigned integer" 
            
            if(WarningFlag == True):
                return "WARNING"
                
            if(a > REGFILESIZE):                                            #if the value goes more than allowed bitsize 
                print("WARNING in line "+str(LineNumber)+": Register value greater than "+ str(REGFILESIZE)+" is not accepted - "+asm)
                return "WARNING"
            machineCode += bin(a).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'
            machineCode += descriptionMnemonics[3]+'_'
            machineCode += bin(b).split('0b')[1].rjust(OFFSETBITWIDTH,'0')                   
            
        #----------------------------------------------- jump ---------------------------------------------#
        else:                              #jr rs
            if(len(values) != 2):
               print("WARNING in line "+str(LineNumber)+": -"+str(asm)+"- is missing some parameters")
               return "WARNING"
            a =  registerValue(values[1],asm,LineNumber)
            if(WarningFlag):
                return "WARNING"
                
            if(a > REGFILESIZE):                                              #if the value goes more than allowed bitsize 
                print("WARNING in line "+str(LineNumber)+": Register value greater than "+ str(REGFILESIZE)+" is not accepted - "+asm)
                return "WARNING"
            machineCode += bin(a).split('0b')[1].rjust(REGBITWIDTH,'0')+'_'
            machineCode += bin(0).split('0b')[1].rjust(3*REGBITWIDTH,'0')+'_'
            machineCode += descriptionMnemonics[3]
            
    #--------------------------------------- For the asm that requires no register values -------------------------#  
    else: #j target
        if(len(values) != 2):
           print("WARNING in line "+str(LineNumber)+": -"+str(asm)+"- is missing some parameters")
           return "WARNING"
       
        tmpa = OffsetCalculator(values[1],CurrentMem,asm,LineNumber,True) #True indicate target position to be calculated rather than offset 
        a =  NegToPosINT(tmpa,TARGETBITWIDTH,LineNumber)          
        if(WarningFlag):
            return "WARNING"
        machineCode += bin(a).split('0b')[1].rjust(TARGETBITWIDTH,'0')
      
    return machineCode
    
#==================================================================================================================#    
    
    
    
    
    
    
#========================================== Underscore Remover ======================================================#
#   This fuction takes in a string and removes the '_' if present. It helps in converting the  
#   human readable, formatted binary code to binary or hex
#==================================================================================================================#
def underscoreRemover(text,LineNumber):
    ftext = ''                                      #formatted Text
    for c in text:
        if c != '_':
            ftext += c
    
    try:
        return hex(int(ftext,2))
    except ValueError:
        print("WARNING in line "+str(LineNumber)+": Cannot convert to hex")
        return "WARNING"
#==================================================================================================================#    







#=========================================    Main Program part-1  ======================================================#   
#   Iterating for all line till End of Line of input is reached. It is mainly to read all the tags and their
#   location on the code as well as extracting the assembly program from the comments and others
#   NOTE:readline() will return '' for eof and \n for a newline
#==================================================================================================================#   
try:
    tmpwhandler = open(TMP,'w')
    fp = open(INPATH,'r')
    LineNumber = 0
    CurrentMem = int(MemDictionary['root'])       #Holds the memory locatiom the current asm 
    asm = ''                                      #Holds the assembly codes
    WarningCount = 0
    for line in iter(lambda: fp.readline(), ''):  #iterating throughout the file till EOF
        words = line.split("\n")[0].split("#")[0].split("\r")[0] #extrating wording from eol,comments and other extras
        LineNumber +=1
        if not words:                             #if line is empty
            continue
        #---------------------------------------------------------------------------------------------#
        #  This piece of code is trying to extract relative path (if exist add value to dictionary) 
        #  and assembly code
        #---------------------------------------------------------------------------------------------#
        if(words.find(':')>0):                    #if there is a relative path
            pieces = words.split(":")
            if(len(pieces) > 2):
                print("ERROR-"+str(LineNumber)+": There are more relative path symbol(:) -"+words+"\nTerminating the program.....")
                sys.exit(1)
            else:
                RelPath = pieces[0].strip()      #adding values of RelPath to dictionary + removing spaces start and end of string
                if RelPath in MemDictionary:    
                    print("WARNING in line "+str(LineNumber)+": There are multiple entries for "+RelPath+", values may get overwritten" )
                    WarningCount += 1
                else:
                    MemDictionary[RelPath] = CurrentMem #Updating  on the memory dictionary
                asm = pieces[1].strip()         #removing spaces start and end of string
        else:
            asm = words.strip()
            
        if not asm:                             #if asm is empty i.e ''
            continue
        CurrentMem += 1                         #updating Memory Position    
        tmpwhandler.write(str(LineNumber)+'='+asm+'\n')
         
    tmpwhandler.close()
    fp.close()
except IOError:
    print("ERROR: File in path "+INPATH+" not found"+"\nTerminating the program.....")
#==================================================================================================================#  





    

#========================================= Main Program part-2  ======================================================#   
#   Iterating for all line till End of Line of 'TMP' is reached. It will convert the assembly code 
#   NOTE:readline() will return '' for eof and \n for a newline
#==================================================================================================================#    
try:
    outhandler = open(OUTPUT,'w')
    tmprhandler = open(TMP,'r')
    CurrentMem = int(MemDictionary['root'])       #Holds the memory locatiom the current asm 
    asm = ''                                      #Holds the assembly codes
    
    for line in tmprhandler:
        asm = line.rstrip().split('=')[1]   
        LineNumber = int(line.rstrip().split('=')[0].split()[0])
        MachineHex = assemblyConverter(asm,CurrentMem,LineNumber)
        CurrentMem += 1                           #updating Memory Position 
        output = asm.ljust(30,' ') +': '
        if (MachineHex =='WARNING'):
            WarningCount += 1
            output+= 'WARNING'.ljust(15,' ')+' : '
        else:
            output+= underscoreRemover(MachineHex,LineNumber).ljust(15,' ')+' : '
         
        output+=MachineHex
        outhandler.write(output+'\n')

    tmprhandler.close()
    outhandler.close()
except IOError:
    print("ERROR: run time generated files were deleted. Re-run the program.\nTerminating the program.....")
    
    

if(WarningCount == 0):
    print("Program succesfully compiled and translated for MIPS R2000")
    print("Output generated in "+str(OUTPUT)+" which is formatted as \"asm : HEX : binary\" ")
else:
    print("Program encountered "+str(WarningCount)+" warnings while translating")

#============================================= The End ============================================================#  

