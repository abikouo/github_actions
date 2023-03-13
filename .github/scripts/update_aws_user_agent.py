#!/usr/bin/env python3

from pathlib import PosixPath
import yaml
import logging
import re

FORMAT = '[%(asctime)s] - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('update_aws_user_agent')
logger.setLevel(logging.DEBUG)

def update_user_agent(src, var_name, galaxy_version):
    VARIABLE_RE = r"^%s = [\"|'](.*)[\"|']" % var_name
    new_content = []
    updated = False
    with src.open() as fd:
        for line in fd.read().split("\n"):
            m = re.match(VARIABLE_RE, line)
            if m and m.group(1) != galaxy_version:
                updated = True
                logger.info("Update '%s' from file '%s', current='%s', new='%s'" % (
                    var_name,
                    src.stem,
                    m.group(1),
                    galaxy_version
                ))
                new_content.append('%s = "%s"' % (var_name, galaxy_version))
            else:
                new_content.append(line)

    if updated:
        src.write_text("\n".join(new_content))
    return updated


def update_collection_user_agent(var_name, galaxy_version):

    def _get_files_from_directory(path):
        if not path.is_dir():
            return [path]
        result = []
        for p in path.iterdir():
            result.extend(_get_files_from_directory(p))
        return result

    return any(
        update_user_agent(src, var_name, galaxy_version)
        for src in _get_files_from_directory(PosixPath("plugins")) if str(src).endswith(".py")
    )

def read_collection_info():
    with PosixPath("galaxy.yml").open() as fd:
        return yaml.safe_load(fd)

def main():
    collection_info = read_collection_info()
    logger.info(f"collection information from galaxy.yml: {collection_info}")
    variable_name = collection_info["namespace"].upper() + "_" + collection_info["name"].upper() + "_COLLECTION_VERSION"
    logger.info(f"Expecting collection user-agent variable => '{variable_name}'")

    galaxy_version = collection_info["version"]
    update_collection_user_agent(variable_name, galaxy_version)

if __name__ == "__main__":

    main()