from functools import lru_cache
import pathlib

from reportengine.compat import yaml

path_vpdata = pathlib.Path(__file__).parent
path_commondata = pathlib.Path(__file__).with_name('commondata')
path_new_commondata = pathlib.Path(__file__).with_name('new_commondata')
path_theorydb = pathlib.Path(__file__).with_name('theory.db')

# VP should not have access to this file, only to the products
_path_legacy_mapping = path_new_commondata / "dataset_names.yml"
legacy_to_new_mapping = yaml.YAML().load(_path_legacy_mapping)


@lru_cache
def new_to_legacy_map(dataset_name, variant_used):
    """Loop over the dictionary and fing the right dataset"""
    # It is not possible to reverse the dictionary because
    # we can have 2 old dataset mapped to the same new one

    possible_match = None
    for old_name, new_name in legacy_to_new_mapping.items():
        variant = None
        if not isinstance(new_name, str):
            variant = new_name.get("variant")
            new_name = new_name["dataset"]

        if new_name == dataset_name:
            if variant_used == variant:
                return old_name
            # Now, for legacy variants we might want to match (sys,)
            # so accept anything that starts with `legacy_`
            # so variant `legacy_10` will match `legacy` in the dictionary
            # but if an exact match if found before, the search ends
            if variant_used is not None and variant_used.startswith("legacy_"):
                possible_match = old_name

    return possible_match
