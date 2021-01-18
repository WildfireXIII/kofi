import glob
import os
import re

from kofi import util

LINK_PATTERN = re.compile("\[.*\]\((.*\.md)\)")


class Map:
    def __init__(self):
        # [key:A] -> B
        # key is a file, value is array of files that key file links to
        self.links_to = {}  

        # A -> [key:B]
        # key is a file, value is array of files that link _to_ this file
        self.links_from = {}
        self.links_from = {}
        self.links_from = {}
        self.links_from = {}
        self.links_from = {}
        self.links_from = {}
        self.links_from = {}

        self.filetitles = {}

        # any paths in here are unfound/dead, don't output them
        self.dead_paths = [] 

    def construct_map(
        self, root=None, ignore_recent=True, ignore_inbox=True, grab_titles=True
    ):
        # NOTE: use root = None to construct the map of _all_ notes
        util.log(f"Constructing map from root {root}", "map.py")
        active_dir = util.run_shell("kofi-active-dir")
        os.chdir(active_dir)

        if root is None:
            for filepath in glob.iglob("*.md"):
                if self.handle_path(filepath, ignore_recent, ignore_inbox, grab_titles):
                    # scan the file for links
                    self.parse_file_links(filepath)
        else:
            self.handle_path(root)

            with open(root, "r") as infile:
                contents = infile.read()

                matches = re.findall(LINK_PATTERN, contents)
                for match in matches:
                    link = match

                    if self.handle_path(link, ignore_recent, ignore_inbox, grab_titles):
                        self.create_link(root, link)
                        # go one level deep
                        self.parse_file_links(link)

    def handle_path(
        self, filepath, ignore_recent=True, ignore_inbox=True, grab_titles=True
    ):
        """ Go through the standard things that each file needs to go through """
        if filepath == "recent.md" and ignore_recent:
            return False
        if filepath == "inbox.md" and ignore_inbox:
            return False
        if util.run_shell_silent_error("kofi-get-property", "hidden", filepath) == "true":
            return False

        if grab_titles:
            title = util.run_shell_silent_error("kofi-get-title", filepath)
            self.filetitles[filepath] = title

        if filepath not in self.links_to:
            self.links_to[filepath] = []

        if filepath not in self.links_from:
            self.links_from[filepath] = []

        return True

    def parse_file_links(self, filepath, grab_titles=True):
        try:
            with open(filepath, "r") as infile:
                contents = infile.read()

                matches = re.findall(LINK_PATTERN, contents)
                for match in matches:
                    link = match
                    if self.handle_path(link):
                        self.create_link(filepath, link)
        except FileNotFoundError:
            # skipping an unfound link
            util.log(f"Map skipping file could not find: {filepath}", "map.py", level="warn")
            # remove from map
            self.remove_path(filepath)

    # file_from is a
    # file_to is b
    # A -> B
    def create_link(self, a, b):
        # file_from (a) is key in links_to, file_to (b) is added to values
        if a not in self.links_to:
            self.links_to[a] = []

        self.links_to[a].append(b)

        # (b) is key in links_from, file_from (a) is added to values
        if b not in self.links_from:
            self.links_from[b] = []

        self.links_from[b].append(a)

    # "undoes" any links to or from the given path
    # TODO: I don't think it will be removed from any other arrays though.
    def remove_path(self, a):
        self.dead_paths.append(a)
        if a in self.links_to:
            del self.links_to[a]
        if a in self.filetitles:
            del self.filetitles[a]
        if a in self.links_from:
            del self.links_from[a]

    def to_graphviz(self):
        lines = ["strict digraph G", "{", 'bgcolor="transparent"', 'overlap="false"']

        for item in self.filetitles:
            link = item[: item.rfind(".")] + ".html"
            lines.append(f'"{item}" [ label="{self.filetitles[item]}" URL="{link}" ];')

        already_handled = []

        for item in self.links_to:
            for end in self.links_to[item]:
                if end in self.dead_paths: 
                    continue
                if (item, end) in already_handled:
                    continue

                if item in self.links_to[end]:
                    lines.append(f'"{item}" -> "{end}"[dir=both]')
                    already_handled.append((end, item))
                else:
                    lines.append(f'"{item}" -> "{end}"')

        lines.append("}")

        graph = "\n".join(lines)

        return graph
