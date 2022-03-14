"""
Created on Mar 14, 2022

@author: Benedikt Ursprung
"""


def table2html(
    data_table, header=[], markup='border="0" alignment="center", cellspacing="2"'
):
    if len(data_table) == 0:
        return ""
    text = f"<table {markup}>"
    if len(header) == len(data_table[0]):
        text += '<tr align="left">'
        for element in header:
            text += "<th>{} </th>".format(element)
        text += "</tr>"
    for line in data_table:
        text += "<tr>"
        for element in line:
            text += f"<td>{element} </td>"
        text += "</tr>"
    text += "</table>"
    return text


def dict2htmltable(
    data_dict, markup='border="0", cellspacing="1", cellpadding="3", vertical'
):
    if len(data_dict) == 0:
        return ""
    text = f'<table {markup}><tr><th alignment="right">key</th><th>values</th></tr>'
    for k, v in data_dict.items():
        text += (
            f'<tr><td  alignment="right">{k}</td><td align="right">{v:10.3f}</td></tr>'
        )
    text += "</table>"
    return text
