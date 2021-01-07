# MIPS-Assembler
 This assembler takes in assembly program written _@INPATH_, checks for warnings and converts to MIPS (Single cycle execution) HEX aswell as (R/J/I type formatted) readable binary codes to _@OUTPUT_.

>Feature summary:
>  * understands "goto TAGS" 
>  * detects warning/mistakes and points line  
>  * customisable assembler for MIPS 


# HIGHLIGHTS:
  1. It can understand "goto TAGS" written for offset and jump statements. The line is tagged by *\'\<tagname\> : \<asm\>\'*  
```
     eg: START: ..
                ..
                bne $s1, $s2, START  # relative position
                ..
                j START              # absolute position
```

  2. It can detect missing paranthesis, commas, register values or (if valid) typos and point line where they occured as well as probable mistake. In the previous assembly code, if **START** tag is not initialised in that begining but used in the code then it gives warning as follows  \
  `WARNING in line no. : @START is not found in the program `  \
      More such error and detection can be found in the test folder.
      
  3. It can be customised to be used for machines using different opcodes, register, function values/bitwidth or different names for operations (mneumatics) as long as these are used for machines under MIPS family. The opcodes and other values can be changed in 'mneumatics.dict' and 'regNames.dict'.  This code needs these two files for reference as it is neither coupled with opcodes or mneumonics. The @input and @output paths/ bitwidths can be changed in the code under the section **PATH Variables and Constants Used**.
