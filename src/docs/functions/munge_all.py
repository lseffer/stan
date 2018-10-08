#!/usr/bin/python

#  keeps track of chapter, section
#  finds all function definitions (latex tag 'fitem')
#  gets arguments, descriptions
#  writes each chapter as Rmd
#  handles labels

import os
import os.path
import re
import sys

rstudioOut = "rstudio_listing.txt"
rmdDir = "pages"
texfile = "preproc_all.tex"

def main():
    if (not os.path.exists(rstudioOut)):
        fh1 = open(rstudioOut, 'w+')
        fh1.close()
        
    if not os.path.isfile(texfile):
        print("File {} does not exist. Exiting...".format(texfile))
        sys.exit()
    
    chapterRmd = ""
    with open(texfile) as fp:
        for line in fp:
            line = line.strip()
            if (len(line) == 0):
                continue
            if (line.startswith("\\part")):
                process_part(line)
            elif (line.startswith("\\chapter")):
                chapterName = get_name(line)
                chapterLabel = get_label(line)
                sectionName = ""
                chapterRmd = chapter_rmd_page(chapterName, chapterLabel)
            elif (line.startswith("\\section")):
                process_section(line, chapterRmd)
            elif(line.startswith("\\begin{description}")):
                process_description(line, chapterRmd)
            elif (line.startswith("\\sub")):
                process_subsection(line, chapterRmd)
            else:
                process_line(line, chapterRmd)
    fp.close()

def process_description(line, rmdPath):
    line = remove_tags(line, "farg")
    line = remove_tags(line, "mbox")
    line = munge_code(line)
    items = line.strip().split("\\fitem")
    for item in items:
        if (item.startswith("\\begin")):
            continue
        else:
            numLines = 1
            if (item.startswith("two")):
                numLines = 2
            elif (item.startswith("three")):
                numLines = 3
            elif (item.startswith("four")):
                numLines = 4
            elif (item.startswith("Unary")):
                open1 = item.find("{")
                close = item.find("}")
                open2 = item.find("{",close)
                name = item[open1 : close + 1]
                rest = item[close : len(item)]
                item = "{R}" + name + "{T x}" + rest
            endIdx = item.find("\\end{description}")
            if (endIdx > 0):
                item = item[0 : endIdx]
            item = ' '.join(item.split())
            item_dict = process_item(item, numLines)
            write_item(item_dict, rmdPath)
    
def process_item(item, numLines):
    curIdx = 0
    openBrace = str.find(item, "{", curIdx)
    if (openBrace < 0):
        print "ERROR parsing return type: ", item
        return
    closeBrace = str.find(item, "}", openBrace+1)
    if (closeBrace < 0):
        print "ERROR parsing return type: ", item
        return
    return_type = item[openBrace+1 : closeBrace]

    # get name
    curIdx = closeBrace
    openBrace = str.find(item, "{", curIdx)
    if (openBrace < 0):
        print "ERROR parsing name: ", item
        return
    closeBrace = str.find(item, "}", openBrace+1)
    if (closeBrace < 0):
        print "ERROR parsing name: ", item
        return
    name = item[openBrace+1 : closeBrace]

    # get args
    argsAll = ""
    for x in range(0, numLines):
        curIdx = closeBrace
        openBrace = str.find(item, "{", curIdx)
        if (openBrace < 0):
            print "ERROR parsing args: ", item
            return
        closeBrace = match_close(item, openBrace+1)
        if (closeBrace < 0):
            print "ERROR parsing args: ", item
            return
        args = item[openBrace+1 : closeBrace]
        argsAll += args
        if (x < numLines - 1):
            argsAll += ", "
    
    # get decscription
    desc = ""
    curIdx = closeBrace
    openBrace = str.find(item, "{", curIdx)
    if (openBrace > 0):
        closeBrace = match_close(item, openBrace+1)
    if (openBrace > 0 and closeBrace > 0):
        desc = item[openBrace+1 : closeBrace]

    return {"name":name,
            "return_type":return_type,
            "args":argsAll,
            "description":desc}

def process_section(line, rmdPath):
    sectionName = get_name(line)
    label = get_label(line)
    fh = open(rmdPath, 'a')
    fh.write("## %s" % sectionName)
    if (len(label) > 0):
        fh.write(" {#%s}" % label)
    fh.write("\n\n")
    fh.close()

def process_subsection(line, rmdPath):
    start = line.find("{")
    end = line.find("}",start)
    tag = line[0:start]
    ct = tag.count("sub") + 2
    name = line[start+1:end]
    label = get_label(line)
    fh = open(rmdPath, 'a')
    fh.write('#' * ct)
    fh.write(" %s" % name)
    if (len(label) > 0):
        fh.write(" {#%s}" % label)
    fh.write("\n\n")
    fh.close()

def process_line(line, curPage):
    if line.startswith("```"): # stan code
        lines = line.split("\\n")
        line = '\n'.join(lines)
    else:
        line = remove_tags(line, "farg")
        line = munge_code(line)
    fh = open(curPage, 'a')
    if line.startswith("|"):  # table
        fh.write("%s\n" % line) 
    else:                     # paragraph
        fh.write("%s\n\n" % line)  
    fh.close()

def process_part(line):
    part = get_name(line)
    rmdFile = ''.join([str.lower(part).replace(" ","_"), ".Rmd"])
    rmdPath = os.path.join(rmdDir, rmdFile)
    if (not os.path.exists(rmdPath)):
        fh = open(rmdPath, 'w+')
        fh.write("# <i style=\"font-size: 110%; padding:1.5em 0 0 0; color:#990017;\">")
        fh.write(part)
        fh.write("</i> {-}\n")
        fh.close()
    print rmdPath
    
def chapter_rmd_page(chapterName, label):
    filename = str.lower(chapterName).replace(" ","_")
    filename = filename.replace("(","")
    filename = filename.replace(")","")
    filename = filename.replace(",","")
    rmdFile = ''.join([filename, ".Rmd"])
    if (not os.path.exists(rmdDir)):
        os.makedirs(rmdDir)
    rmdPath = os.path.join(rmdDir, rmdFile)
    if (not os.path.exists(rmdPath)):
        fh = open(rmdPath, 'w+')
        fh.write("# %s" % chapterName)
        if (len(label) > 0):
            fh.write(" {#%s}" % label)
        fh.write("\n\n")
        fh.close()
        print rmdPath
    return rmdPath

def write_item(item_dict, rmdPath):
    fh = open(rstudioOut, 'a')
    if (len(item_dict["args"]) == 0):
        fh.write("`%s`; `%s`; (); %s\n" % (item_dict["return_type"], item_dict["name"], item_dict["description"]))
    else:
        fh.write("`%s`; `%s`; (`%s`); %s\n" % (item_dict["return_type"], item_dict["name"], item_dict["args"], item_dict["description"]))
    fh.write("\n")
    fh.close()
    fh = open(rmdPath, 'a')
    if (len(item_dict["args"]) == 0):
        fh.write("`%s` **`%s`**()\n%s\n" % (item_dict["return_type"], item_dict["name"], item_dict["description"]))
    else:
        fh.write("`%s` **`%s`**(`%s`)\n%s\n" % (item_dict["return_type"], item_dict["name"], item_dict["args"], item_dict["description"]))
    fh.write("\n")
    fh.close()


def munge_code(line):
    p = re.compile("\code{")
    while True:
        if re.search(p, line):
            line = code2backtick(line)
        else:
            break
    return line

def code2backtick(text):
    start = str.find(text, "\code{")
    if (start < 0):
        return text
    end = match_close(text, start+6)
    if (end < 0):
        return text
    if (end == len(text)):
        return text[0 : start] + "`" + text[start + 6 : end] + "`"
    else:
        return text[0 : start] + "`" + text[start + 6 : end] + "`" + text[end+1 : len(text)]        

def remove_tags(text, tag):
    pat = ''.join(["\\\\",tag,"{"])
    while True:
        if re.search(pat, text):
            text = remove_tag(text, tag)
        else:
            break
    return text

def remove_tag(text, tag):
    pat = ''.join(['\\',tag,'{'])
    start = str.find(text, pat)
    if (start < 0):
        return text
    end = match_close(text, start+len(tag)+3)
    if (end < 0):
        return text
    return text[0 : start] + text[start + len(tag) + 2 : end] + text[end+1 : len(text)]


def match_close(item, startIdx):
    level = 0
    for x in range(startIdx, len(item)):
        if item[x] == '{':
            level += 1
        elif item[x] == '}':
            if (level == 0):
                return x
            else:
                level -= 1
    return -1

def get_name(line):
    p = re.compile('\{[^}]*')
    name = p.search(line).group()
    return name[1 : len(name)]

def get_label(line):
    start = str.find(line, "\label{")
    if (start < 0):
        return ""
    end = str.find(line, ".", start)
    return line[start+7 : end]


def clean(name):
    if (name.endswith("_cdf")):
        return name[0:(len(name)-4)]
    if (name.endswith("_lccdf")):
        return name[0:(len(name)-6)]
    if (name.endswith("_lcdf")):
        return name[0:(len(name)-5)]
    if (name.endswith("_lpdf")):
        return name[0:(len(name)-5)]
    if (name.endswith("_lpmf")):
        return name[0:(len(name)-5)]
    if (name.endswith("_rng")):
        return name[0:(len(name)-4)]
    if (not name.startswith("operator")):
        return name
    name = name.replace("==","_logial_equal")
    name = name.replace("!=","_logical_not_equal")
    name = name.replace("!","_negation")
    name = name.replace("<=","_logical_less_than_equal")
    name = name.replace("<","_logical_less_than")
    name = name.replace(">=","_logical_greater_than_equal")
    name = name.replace(">","_logical_greater_than")
    name = name.replace("&&","_logical_and")
    name = name.replace("||","_logical_or")
    if (name.endswith("=")):
        name = name.replace("operator","operator_compound")
        name = name[0 : len(name) - 1]
    name = name.replace("^","_pow")
    name = name.replace("%","_mod")
    name = name.replace("'","_transpose")
    name = name.replace(".","_elt")
    name = name.replace("*","_multiply")
    name = name.replace("/","_divide")
    name = name.replace("+","_add")
    name = name.replace("-","_subtract")
    name = name.replace("\\","_left_div")
    return name


if __name__ == '__main__':  
    main()
