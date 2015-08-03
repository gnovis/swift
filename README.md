# Swift - FCA Data Converter

## Expected parameters
-------------------

### a. non-scale (attributes and objects)
String with values sepeprated by: ",", separator inside string must be escaped e.g Example: ```"name, age, sex, nation\,ality"```

 * string with values and types(s-string, n-numeric, e-enumeration data) separated by: ","
 * Example: ```"name[s], age[n], sex[e], nation\,ality[s]"```

### b. scale (attributes)
 * string with formulas seperated by: ","
   * formula in format:	```new_attr=old_attr[expression]identifier```
     * new_attr = name of new attribute witch will be the result of a conversion
     * old_attr = name of attribute, whitch will be use as template for new attribute
     * expression = string(for enum data), 
				    regular expression(for string data), 
				    interval(for numeric data) e.g ```x>=50 or 100<value<150```
     * identifier = s - string data
					n - numeric data
					e - enumeration data
 
   * formula in format ```new_attr=old_attr```
     * result of scaling will be same value
     * it works (and make sance) only for binary values 0 and 1
 
 * Example: ```"scaled_age=age(x<50)i, 
				scaled_sex=sex(woman)e, 
				sclaed_height=height(150<=x<=210)i
				scaled_same=same, 
				scaled_address=address(\w? street[0-9]+)s"```
### c. others
 * e.g separator, classes ...


## Requirements
------------
* python3
* PyQt4