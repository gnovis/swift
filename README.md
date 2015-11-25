# **Swift - FCA Data Converter** ![](swift_fca/resources/images/swift_icon.ico?raw=true "Swift FCA")

Converter of data formats used in Formal Concept Analysis and public repositories. Swift provides console application and GUI interface.  

## Supported formats
* [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) 
* [ARFF](http://weka.wikispaces.com/ARFF+%28book+version%29)
* [DATA](http://www.cs.washington.edu/dm/vfml/appendixes/c45.htm)
* [DAT](http://fcalgs.sourceforge.net/format.html)
* [CXT](http://www.upriss.org.uk/fca/fcafileformats.html#Burmeister)

## Arguments

### A. Object Names
List of object names sepeprated by: ",", separator inside string isn't allowed.  
Example: `"obj1, obj2, obj3, ... "`  

### B. Attributes  

#### Grammar (BNF with [regular expressions](https://docs.python.org/2/library/re.html))

```
<formulas> ::= <formula> | (<formula> ";" <formulas>)
<formula> ::= (<names> "=")? <names> ((":" <type> ("[" <scale>? "]")?) | "[]")?
<names> ::= <name> | (<name> "," <names>)
<type> ::= "n" | "e" | "s" | ("d" ("/" <date_format>)?)
<scale> ::= <num_scale> | <enum_scale> | <str_scale> | <date_scale> | <bin_vals>
<name> ::= \w+ | ((\d+)? "-" (\d+)?) | "*"
<date_format> ::= "F="? "'" .+ "'"
<num_scale> ::= (<var> <op> <num_val>) | (<num_val> <op> <var>) |
                (<num_val> <op> <var> <op> <num_val>)
<enum_scale> ::= "'" \w+ "'"
<str_scale> ::= "'" .+ "'"
<date_scale> ::= ((<var> <op> <date_val>) | (<date_val> <op> <var>) |
                 (<date_val> <op> <var> <op> <date_val>))
<bin_vals> ::= ("0="? "'" .* "'" ",")? "1="? "'" .+ "'"
<var> ::= [a-zA-Z_]+
<op> ::= "<" | ">" | "<=" | ">=" | "=" | "!="
<num_val> ::= "-"? \d+
<date_val> ::= "'" .+ "'"
```
*Notes: Every token can be surrounded by any amount of white spaces. In grammar are white spaces omitted because of better readability.*  

**Attributes**  
Attributes are compound of formulas separated by: ","  

**Formula**  
Formula has format: `new_name=old_name[arguments]` or `old_name[arguments]`  

`new_name` = name of new attribute which will be the result of a conversion. If this new name and `=` is ommited, name of scaled attribute will be old name.  
`old_name` = name of attribute, which will be use as template for new attribute  
`arguments` = list of arguments separated by "," which depends on attribute type or can be omitted (explanation below)  

Attribute Type is on a first position of `arguments`:

* s - String
* n - Numeric
* e - Enumeration 
* d - Date  

Valid syntax of formula is also: `new_attr=old_attr[]`, in this case result of scaling will be same value, it works (and make seance) only for binary values 0 and 1  

**String Attribute**  
`attributes = s, 'regular_expression'`   
`regular_expression`: must be surrounded by quotes. Supported syntax is described here: [python regex](https://docs.python.org/2/library/re.html)  
For Scaling is used `re.RegexObject.search` method.  
Description from [documentation](https://docs.python.org/2/library/re.html#re.RegexObject.search):  
> Scan through string looking for a location where this regular expression produces a match, and return a corresponding MatchObject instance (Scaling return True). Return None if no position in the string matches the pattern (Scaling return False)  

**Numeric Attribute**  
`attributes = n, bool_expression`  
`bool_expression`: is compound of variable(any alphas name), number, and operators(`<`, `>`, `>=`, `<=`, `==`), allowed are following forms:

* variable operator number -> `var >= 50`
* number operator variable -> `66 == var`
* number operator variable operator number -> `10 < var < 100`

**Enumeration Attribute**  
`attributes = e, pattern`  
`pattern`: literal which exact match one of item in enumeration  

**Date Attribute**  
`attributes = d, bool_expr, 'date_format'`  
`bool_expr`: has same syntax as bool_expr in Numeric Attribute, but number is Unix Time Stamp  
`date_format`: must be surrounded by quotes. Supported syntax is described here: [python datetime](https://docs.python.org/2/library/datetime.html#module-datetime)
 
Example: 
```
"scaled_age=age[n, x<50], 
 scaled_sex=sex[e, woman], 
 scaled_height=height[n, 150<=x<=210],  
 scaled_same=same[],
 old_name[n, val>50], 
 scaled_address=address[s, '\w? street[0-9]+'],
 scaled_birthday=birthday[d, date > 1000, '%H:%M:%S %Z']"
```

### C. Others
e.g separator, classes,  ...


## Requirements
* [python3](https://www.python.org/)
* [PyQt4](http://www.riverbankcomputing.co.uk/software/pyqt/intro)
* [pyparsing](https://pyparsing.wikispaces.com/)
