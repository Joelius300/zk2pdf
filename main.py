import json
import fire
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Note:
    title: str
    id: str
    path: Path
    body: str


format_str = '{ "title": {{json title}}, "id": "{{metadata.id}}", "path": {{json path}}, "body": {{json body}} }'


def format_to_note(formatted_output: str):
    as_dict = json.loads(formatted_output)
    as_dict['path'] = Path(as_dict['path'])
    return Note(**as_dict)


def get_output(*args: str):
    command = ["zk", *args]
    # print(" ".join(command))
    out = subprocess.run(command, capture_output=True, text=True, check=True)
    return out.stdout


def output_to_notes(output: str):
    lines = output.splitlines()
    return [format_to_note(line) for line in lines]


def create_docs(tag: str, link_depth: int = 0, sort=True):
    boilerplate_args = ["--format", format_str, "-q", "--no-pager", "--sort", "path"]
    tagged_notes = get_output("list", "-t", tag, *boilerplate_args)
    tagged_notes = output_to_notes(tagged_notes)
    if link_depth > 0:
        # fetch notes that are linked by the tagged notes up to a certain recursive depth
        linked_notes = get_output("list", "--linked-by", ','.join([note.id for note in tagged_notes]),
                                  "-t", f"NOT {tag}", "--max-distance", str(link_depth), *boilerplate_args)
        linked_notes = output_to_notes(linked_notes)
    else:
        linked_notes = []

    all_notes = tagged_notes + linked_notes
    all_notes = [n for n in all_notes if n.title != tag]  # we don't care about the index note where title==tag
    if sort:
        all_notes = list(sorted(all_notes, key=lambda n: n.title.lower()))  # sort alphabetically by title

    id_replacement = {f'[{n.id}]': n.title for n in all_notes}
    compiled_regex = re.compile("|".join(map(re.escape, id_replacement)))
    for note in all_notes:
        # replace [[id]] with [title] in body if there is a note with the appropriate title.
        # for printing, it's irrelevant but pandoc also creates links to the appropriate headings when converting.
        note.body = compiled_regex.sub(lambda match: id_replacement[match.group(0)], note.body)

    # header for pandoc conversion (into pdf)
    header = """---
classoption:
- twocolumn
- landscape
geometry:
- margin=1cm
papersize: a4
fontsize: 10pt
---\n
"""

    # combine all the notes into a single markdown file
    combined = header + "\n\n".join(n.body for n in all_notes)
    with open(f"{tag}.md", "wt") as file:
        file.write(combined)

    # the zk is organized in a way where all the modules get their own folder and inside that there is ./img
    # so all of those module folders need to specified as resource paths.
    resource_paths = set(n.path.parts[0] for n in all_notes)
    resource_paths = ":".join(resource_paths)

    subprocess.run(["pandoc", f"{tag}.md", "--from=markdown-implicit_figures",
                    "--resource-path", resource_paths, "-s", "-o", f"{tag}.pdf"])
    # subprocess.run(["pandoc", f"{tag}.md", "--from=markdown-implicit_figures",
    #                 "--resource-path", resource_paths, "-s", "-o", f"{tag}.docx"])


if __name__ == '__main__':
    # if it gets more complicated with args, try Fire!
    # create_docs(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    fire.Fire(create_docs)
