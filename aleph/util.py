# coding: utf-8
import os
import yaml
from celery import Task
from banal import ensure_list
from normality import normalize


PDF_MIME = 'application/pdf'


def match_form(text):
    """Turn a string into a form appropriate for name matching."""
    # The goal of this function is not to retain a readable version of the
    # string, but rather to yield a normalised version suitable for
    # comparisons and machine analysis.
    return normalize(text, lowercase=True, ascii=True)


def load_config_file(file_path):
    """Load a YAML (or JSON) bulk load mapping file."""
    file_path = os.path.abspath(file_path)
    with open(file_path, 'r') as fh:
        data = yaml.load(fh) or {}
    return resolve_includes(file_path, data)


def resolve_includes(file_path, data):
    """Handle include statements in the graph configuration file.

    This allows the YAML graph configuration to be broken into
    multiple smaller fragments that are easier to maintain."""
    if isinstance(data, (list, tuple, set)):
        data = [resolve_includes(file_path, i) for i in data]
    elif isinstance(data, dict):
        include_paths = data.pop('include', [])
        if not isinstance(include_paths, (list, tuple, set)):
            include_paths = [include_paths]
        for include_path in include_paths:
            dir_prefix = os.path.dirname(file_path)
            include_path = os.path.join(dir_prefix, include_path)
            data.update(load_config_file(include_path))
        for key, value in data.items():
            data[key] = resolve_includes(file_path, value)
    return data


def dict_list(data, *keys):
    """Get an entry as a list from a dict. Provide a fallback key."""
    for key in keys:
        if key in data:
            return ensure_list(data[key])
    return []


class SessionTask(Task):

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from aleph.core import db
        db.session.remove()
