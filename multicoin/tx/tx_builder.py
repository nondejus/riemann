import multicoin
from . import tx
from .. import utils
from ..script import serialization


# TODO: Coerce the [expletive] out of everything
# TODO: Check Terminology.
# NB:
# script_sig -> Goes in TxIn.
#   - Legacy only
#   - Contains initial stack (stack_script)
#   - Contains pubey/script revelation
# stack_script -> Goes in script_sig
#   - Legacy only
#   - Contains script that makes initial stack
# script_pubkey -> Goes in TxOut
#   - Also called pk_script, output_script
#   - P2PKH: OP_DUP OP_HASH160 PUSH14 {pkh} OP_EQUALVERIFY OP_CHECKSIG
#   - P2SH: OP_HASH160 {script_hash} OP_EQUAL
#   - P2WPKH: OP_0 PUSH0x14 {pkh}
#   - P2WSH: OP_0 PUSH0x20 {script_hash}
# WitnessStackItem -> Goes in InputWitness
#   - Witness only
#   - Contains a length-prefixed stack item
# InputWitness -> Goes in Witness
#   - A stack associated with a specific input
#   - If spending from p2wsh, the last item is a serialzed script
#   - If spending from p2wpkh, consists of [signature, pubkey]


def make_sh_output_script(script_string, witness=False):
    '''
    str -> bytearray
    '''
    if witness and not multicoin.network.SEGWIT:
        raise ValueError(
            'Network {} does not support witness scripts.'
            .format(multicoin.get_current_network_name()))

    output_script = bytearray()

    script_bytes = serialization.serialize_from_string(script_string)

    if witness:
        script_hash = utils.sha256(script_bytes)
        output_script.extend(multicoin.network.P2WSH_PREFIX)
        output_script.extend(script_hash)
    else:
        script_hash = utils.hash160(script_bytes)
        output_script.extend(b'\xa9')  # OP_HASH160
        output_script.extend(script_hash)
        output_script.extend(b'\87')  # OP_EQUAL

    return output_script


def make_pkh_output_script(pubkey, witness=False):
    '''
    bytearray -> bytearray
    '''
    if witness and not multicoin.network.SEGWIT:
        raise ValueError(
            'Network {} does not support witness scripts.'
            .format(multicoin.get_current_network_name()))

    output_script = bytearray()

    if type(pubkey) is not bytearray and type(pubkey) is not bytes:
        raise ValueError('Unknown pubkey format. '
                         'Expected bytes. Got: {}'.format(type(pubkey)))

    pubkey_hash = utils.hash160(pubkey)

    if witness:
        output_script.extend(multicoin.network.P2WPKH_PREFIX)
        output_script.extend(pubkey_hash)
    else:
        output_script.extend(b'\x76\xa9\x14')  # OP_DUP OP_HASH160 PUSH14
        output_script.extend(pubkey_hash)
        output_script.extend(b'\x88\xac')  # OP_EQUALVERIFY OP_CHECKSIG
    return output_script


def make_p2sh_output_script(script_string):
    return make_sh_output_script(script_string, witness=False)


def make_p2pkh_output_script(pubkey):
    return make_pkh_output_script(pubkey, witness=False)


def make_p2wsh_output_script(script_string):
        return make_sh_output_script(script_string, witness=True)


def make_p2wpkh_output_script(pubkey):
    return make_pkh_output_script(pubkey, witness=True)


def _make_output(value, script):
    '''
    bytes-like, bytes-like -> TxOut
    '''
    return tx.TxOut(value, script)


def make_sh_output(value, script, witness=False):
    '''
    int, str -> TxOut
    '''
    return _make_output(value=utils.i2le_padded(value),
                        script=make_sh_output_script(script, witness))


def make_p2sh_output(value, script):
    return make_sh_output(value, script, witness=False)


def make_p2wsh_output(value, script):
    return make_sh_output(value, script, witness=True)


def make_pkh_output(value, pubkey, witness=False):
    '''
    int, bytearray -> TxOut
    '''
    return _make_output(value=utils.i2le_padded(value),
                        script=make_pkh_output_script(pubkey, witness))


def make_p2pkh_output(value, pubkey):
    return make_pkh_output(value, pubkey, witness=False)


def make_p2wpkh_output(value, pubkey):
    return make_pkh_output(value, pubkey, witness=True)


def make_witness_stack_item(data):
    '''
    bytearray -> WitnessStackItem
    '''
    return tx.WitnessStackItem(item=data)


def make_witness(data_list):
    '''
    list(bytearray) -> InputWitness
    '''
    return tx.InputWitness(
        stack=[make_witness_stack_item(item) for item in data_list])


def make_outpoint(tx_id_le, index):
    '''
    bytearray, int -> Outpoint
    '''
    return tx.Outpoint(tx_id=tx_id_le,
                       index=utils.i2le_padded(index, 4))


def make_script_sig(stack_script, redeem_script):
    '''
    str, str -> bytearray
    '''
    stack_script += ' {}'.format(
        serialization.hex_serialize_from_string(redeem_script))
    return serialization.serialize_from_string(stack_script)


def make_legacy_input(outpoint, stack_script, redeem_script, sequence):
    '''
    Outpoint, str, str, int -> TxIn
    '''
    return tx.TxIn(outpoint=outpoint,
                   stack_script=stack_script,
                   redeem_script=redeem_script,
                   sequence=utils.i2le_padded(sequence, 4))


def make_legacy_input_and_empty_witness(outpoint, stack_script,
                                        redeem_script, sequence):
    '''
    Outpoint, str, str, int -> (TxIn, InputWitness)
    '''
    return (make_legacy_input(outpoint, stack_script, redeem_script, sequence),
            tx.InputWitness(bytearray([0])))


def make_witness_input(outpoint, sequence):
    '''
    Outpoint, int -> TxIn
    '''
    return tx.TxIn(outpoint=outpoint,
                   stack_script=bytearray([0]),
                   redeem_script=bytearray(),
                   sequence=sequence)


def make_witness_input_and_witness(outpoint, sequence, data_list):
    '''
    Outpoint, int, list(bytearray) -> (Input, InputWitness)
    '''
    return (make_witness_input(outpoint, sequence),
            make_witness(data_list))


def make_tx(version, tx_ins, tx_outs, lock_time,
            tx_witnesses=None):

    '''
    int, list(TxIn), list(TxOut), int, list(InputWitness) -> Tx
    '''
    flag = multicoin.network.SEGWIT_TX_FLAG \
        if tx_witnesses is not None else None
    return tx.Tx(version=utils.i2le_padded(version, 4),
                 flag=flag,
                 tx_ins=tx_ins,
                 tx_outs=tx_outs,
                 tx_witnesses=tx_witnesses,
                 lock_time=utils.i2le_padded(lock_time, 4))


def make_mutable_tx(version, tx_ins, tx_outs, lock_time, tx_witnesses=None):
    '''
    int, list(TxIn), list(TxOut), int, list(InputWitness) -> Tx
    '''
    return make_tx(version, tx_ins, tx_outs, lock_time,
                   tx_witnesses=None, make_immutable=True)
