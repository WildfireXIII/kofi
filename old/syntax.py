""" Handles all syntax resolving """

import re

import util

# TODO: add a "resolution depth"?
def resolve_embeddings(text):
    # find all matching {{{UUID}}} syntax
    match_objs = re.finditer(r'\{\{\{([a-z0-9\-]*)\}\}\}', text)
    matches = [match for match in match_objs]

    new_text = text
    replacements = []
    start_offset = 0
    
    # find replacement text for each embedding syntax found
    for match in matches:
        start = match.start() + start_offset
        end = match.end() + start_offset
        match_len = end - start
        obj_id = match.groups(0)[0]

        # read in the object
        replacement_text = util.get_object(obj_id)

        replacements.append((replacement_text, start, end))

        # update the offset for where the next replacement should appear in the string based on length of newly replaced text
        offset_increase = len(replacement_text) - match_len
        start_offset += offset_increase
    
    # fill in all of the replacements
    for replacement in replacements:
        new_text = new_text[:replacement[1]] + replacement[0] + new_text[replacement[2]:]
    
    return new_text




# TODO: it's possible meta data should never really be in the file itself
def extract_meta(text):
    """ Gets all meta data at the top of the object. """
    lines = text.split("\n")

    meta = {}
    
    if lines[0] == "-----":
        current_line = lines[1]
        while current_line != "-----":
            key, value = current_line.split(": ")
            meta[key] = value

    return meta