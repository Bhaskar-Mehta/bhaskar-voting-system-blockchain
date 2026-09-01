"""
Minimal blockchain implementation used to give the vote record a
tamper-evident structure.

This is intentionally simple (no mining/proof-of-work, no networking) -
it's meant to demonstrate the *idea* of a hash-chained, append-only
ledger for a college project, not to be a production blockchain.

Each vote that is cast creates a new Block. A block's hash is computed
from its own data plus the previous block's hash, so changing any past
block (e.g. editing a vote directly in the database) breaks the chain
and can be detected by verify_chain().
"""
import hashlib
import json


def compute_hash(index, timestamp, data, previous_hash, nonce=0):
    """Return the SHA-256 hash for a block's contents."""
    block_string = json.dumps(
        {
            "index": index,
            "timestamp": timestamp,
            "data": data,
            "previous_hash": previous_hash,
            "nonce": nonce,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(block_string.encode("utf-8")).hexdigest()


GENESIS_PREVIOUS_HASH = "0" * 64


def build_genesis_block_fields(timestamp):
    """Return (data, previous_hash, hash) for the first block in the chain."""
    data = {"type": "genesis", "message": "Bhaskar Voting System - Genesis Block"}
    previous_hash = GENESIS_PREVIOUS_HASH
    block_hash = compute_hash(0, timestamp, data, previous_hash)
    return data, previous_hash, block_hash


def build_vote_block_fields(index, timestamp, previous_hash, vote_receipt, candidate_name):
    """
    Return (data, hash) for a new vote block.

    Note: we deliberately store a one-way hash of the voter's identity
    (the vote_receipt) rather than the voter's identity itself, so the
    public chain can be shown without revealing who voted for whom in
    a way that's traceable back to a specific person from the chain
    alone.
    """
    data = {
        "type": "vote",
        "vote_receipt": vote_receipt,
        "candidate": candidate_name,
    }
    block_hash = compute_hash(index, timestamp, data, previous_hash)
    return data, block_hash


def verify_chain(blocks):
    """
    Given an iterable of Block model instances ordered by index,
    re-derive every hash and check the chain is intact.

    Returns (is_valid: bool, first_broken_index: int | None)
    """
    previous_hash = GENESIS_PREVIOUS_HASH
    for block in blocks:
        expected_hash = compute_hash(
            block.index, block.timestamp.isoformat(), block.data, previous_hash, block.nonce
        )
        if block.previous_hash != previous_hash:
            return False, block.index
        if block.hash != expected_hash:
            return False, block.index
        previous_hash = block.hash
    return True, None
