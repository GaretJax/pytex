import os


def is_sublist(sublist, superlist):
    for i in range(len(superlist) - len(sublist) + 1):
        if sublist == superlist[i:i+len(sublist)]:
            return True
    return False


def find_files_of_type(basedir, extensions, exclude_dirs=None, exclude_files=None):
    matches = set()

    if isinstance(extensions, basestring):
        extensions = [extensions]
    extensions = set([str(e) for e in extensions if e])

    exclude_files = set(exclude_files or [])

    for root, dirnames, filenames in os.walk('.'):
        matching = root.lstrip('./')
        if exclude_dirs and matching:
            matching = matching.split('/')
            for p in exclude_dirs:
                if p.startswith('/'):
                    # Check for absolute path
                    p = p.split('/')[1:]
                    if p == matching[:len(p)]:
                        ignore = True
                        break
                else:
                    # Check for directory names anywhere in the path
                    if is_sublist(p.split('/'), matching):
                        ignore = True
                        break
            else:
                ignore = False
            if ignore:
                continue

        for f in filenames:
            if f.rsplit('.', 1)[-1] in extensions:
                if f not in exclude_files:
                    matches.add(os.path.join(root, f))

    return matches
