from Bio import Phylo
from iterpop import iterpop as ip
from lyncs_utils import keydefaultdict
from nanto import isanan, nantonone
import pandas as pd
import string
import typing


def _parse_ancestor_list(raw: str) -> typing.List[int]:
    assert not any(
        c in raw for c in string.whitespace
    ), "Whitespace separated ancestor list not supported."
    try:
        ancestor_list = eval(raw)
        if ancestor_list == [None]:
            return []
        else:
            assert None not in ancestor_list
            return ancestor_list
    except NameError:
        # if ancestor list contains a placeholder string like NONE,
        # it will trigger a NameError when eval'ed
        return []


def alife_dataframe_to_biopython_trees(
    df: pd.DataFrame,
    setup_branch_lengths: bool = False,
) -> typing.List[Phylo.BaseTree.Tree]:

    df = df.copy()

    df['parsed_ancestor_list'] \
        = df['ancestor_list'].apply(_parse_ancestor_list)

    # maps id to node
    def setup_node(id: int) -> Phylo.BaseTree.Clade:
        res = Phylo.BaseTree.Clade()
        res.id = id
        return res
    nodes = keydefaultdict(setup_node)

    # maps id to origin time
    root_nodes = []

    for __, row in df.iterrows():
        node = nodes[row['id']]

        node.origin_time = nantonone(row.get('origin_time', default=None))
        node.name = row.get('name', default=None)
        node.branch_length = nantonone(row.get('branch_length', None))

        if row['parsed_ancestor_list']:
            ancestor_id = ip.popsingleton(row['parsed_ancestor_list'])
            nodes[ancestor_id].clades.append(node)
        else:
            root_nodes.append(node)

    # set up branch lengths
    if setup_branch_lengths:
        for id, parent_node in nodes.items():
            for child_node in parent_node.clades:
                if child_node.branch_length is None and None not in (
                    getattr(child_node, 'origin_time', None),
                    getattr(parent_node, 'origin_time', None),
                ):
                    assert child_node.origin_time >= parent_node.origin_time
                    child_node.branch_length \
                        = child_node.origin_time - parent_node.origin_time

        for root_node in root_nodes:
            if (
                root_node.branch_length is None
                and getattr(root_node, 'origin_time', None) is not None
            ):
                assert not isanan(root_node.origin_time)
                root_node.branch_length = root_node.origin_time

    return([
        Phylo.BaseTree.Tree(root=root_node)
        for root_node in root_nodes
    ])
