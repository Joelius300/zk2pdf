import os
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Note:
    title: str
    id: str
    path: str


format_str = "{{title}};{{metadata.id}};{{path}}"


def format_to_note(formatted_output: str):
    title, id, path = formatted_output.split(";")
    return Note(title=title, id=id, path=path)


def get_output(*args: str):
    command = ["zk", *args]
    out = subprocess.run(command, capture_output=True, text=True, check=True)
    print(os.getcwd())
    print(" ".join(command))
    return out.stdout


def output_to_notes(output: str):
    lines = output.splitlines()
    return [format_to_note(line) for line in lines]


def create_docs(tag: str):
    boilerplate_args = ["--format", format_str, "-q", "--no-pager"]
    tagged_notes = get_output("list", "-t", tag, *boilerplate_args)
    tagged_notes = output_to_notes(tagged_notes)
    linked_notes = get_output("list", "--linked-by", ','.join([note.id for note in tagged_notes]),
                              "-t", f"NOT {tag}", *boilerplate_args)
    linked_notes = output_to_notes(linked_notes)
    print(linked_notes)


if __name__ == '__main__':
    # if it gets more complicated with args, try Fire!
    create_docs(sys.argv[1])
