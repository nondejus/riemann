import unittest
from .. import helpers
from ...tx import tx
from ... import utils


# On chain legacy tx p2sh -> p2pkh tx
# https://blockchain.info/rawtx/0739d0c7b7b7ff5f991e8e3f72a6f5eb56563880df982c4ab813cd71bc7a6a03?format=hex

class TestByteData(unittest.TestCase):

    def setUp(self):
        pass

    def test_iter(self):
        bd = tx.ByteData()
        bd._bytes.extend(b'\x00\x00')
        i = iter(bd)
        next(i)
        next(i)
        self.assertRaises(StopIteration, i.__next__)

    def test_iadd_error(self):
        bd = tx.ByteData()
        with self.assertRaises(TypeError) as context:
            bd += 'alphabet'

        self.assertIn('unsupported operand type(s) for +=: '
                      'ByteData and str', str(context.exception))

    def test_setattr_error(self):
        bd = tx.ByteData()
        bd._make_immutable()
        with self.assertRaises(TypeError) as context:
            bd.a = 'aaaaa'

        self.assertIn('cannot be written to.', str(context.exception))

    def test_repr(self):
        bd = tx.ByteData()
        bd._bytes.extend(b'\xff')

        self.assertEqual(bd.__repr__(), "ByteData: bytearray(b'\\xff')")

    def test_find(self):
        bd = tx.ByteData()
        bd._bytes.extend(b'\xff\xdd\x88')

        self.assertEqual(bd.find(b'\xff'), 0)
        self.assertEqual(bd.find(b'\xdd'), 1)
        self.assertEqual(bd.find(b'\x88'), 2)
        self.assertEqual(bd.find(b'\x00'), -1)

        bd2 = tx.ByteData()
        bd2._bytes.extend(b'\xaa')

        self.assertEqual(bd.find(bd2), -1)


class TestVarInt(unittest.TestCase):

    def setUp(self):
        pass

    def test_one_byte(self):
        res = tx.VarInt(0xfb)
        self.assertEqual(res, b'\xfb')
        self.assertIsInstance(res, tx.VarInt)

    def test_one_byte_boundary(self):
        res = tx.VarInt(0xff)
        self.assertEqual(res, b'\xfd' + b'\xff')
        self.assertIsInstance(res, tx.VarInt)

    def test_two_bytes(self):
        res = tx.VarInt(0xffff)
        self.assertEqual(res, b'\xfd' + (b'\xff' * 2))
        self.assertIsInstance(res, tx.VarInt)

    def test_four_bytes(self):
        res = tx.VarInt(0xffffffff)
        self.assertEqual(res, b'\xfe' + (b'\xff' * 4))
        self.assertIsInstance(res, tx.VarInt)

    def test_eight_bytes(self):
        res = tx.VarInt(0xffffffffffffffff)
        self.assertEqual(res, b'\xff' + (b'\xff' * 8))
        self.assertIsInstance(res, tx.VarInt)

        res = tx.VarInt(0x0123456789abcdef)
        self.assertEqual(res, b'\xff' + b'\xef\xcd\xab\x89\x67\x45\x23\x01')

        res = tx.VarInt(0x234000000000)  # 6 bytes to test padding
        self.assertEqual(res, b'\xff' + b'\x00\x00\x00\x00\x40\x23\x00\x00')

    def test_negative(self):
        with self.assertRaises(ValueError) as context:
            tx.VarInt(-5)

        self.assertIn('VarInt cannot be less than 0.',
                      str(context.exception))

    def test_too_high(self):
        with self.assertRaises(ValueError) as context:
            tx.VarInt(2 ** 64 + 1)

        self.assertIn('VarInt cannot be greater than (2 ** 64) - 1.',
                      str(context.exception))

    def test_copy(self):
        res = tx.VarInt(0xffffffffffffffff)
        copy = res.copy()
        self.assertEqual(res, copy)
        self.assertIsNot(res, copy)

    def test_from_bytes(self):

        # This test is kinda a joke
        self.assertEqual(tx.VarInt.from_bytes(b'\xfd\x91#'), b'\xfd\x91#')
        self.assertEqual(tx.VarInt.from_bytes(b'\x00'), b'\x00')

        with self.assertRaises(ValueError) as context:
            tx.VarInt.from_bytes(b'\xfe')
        self.assertIn(
            'Malformed VarInt. Got: fe',
            str(context.exception))


class TestOutpoint(unittest.TestCase):

    def setUp(self):
        pass

    def test_create_outpoint(self):
        outpoint_index = helpers.outpoint_index
        outpoint_tx_id = helpers.outpoint_tx_id

        outpoint = tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertEqual(outpoint.tx_id, outpoint_tx_id)
        self.assertEqual(outpoint.index, outpoint_index)
        self.assertEqual(outpoint, outpoint_tx_id + outpoint_index)

    def test_create_outpoint_short_tx_id(self):
        outpoint_index = helpers.outpoint_index
        outpoint_tx_id = bytearray(b'\xff')

        with self.assertRaises(ValueError) as context:
            tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertIn('Expected byte-like object with length 32. ',
                      str(context.exception))

    def test_create_outpoint_str_tx_id(self):
        outpoint_index = helpers.outpoint_index
        outpoint_tx_id = 'Hello world'

        with self.assertRaises(ValueError) as context:
            tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_create_outpoint_long_index(self):
        outpoint_index = utils.i2le_padded(0, 5)
        outpoint_tx_id = helpers.outpoint_tx_id

        with self.assertRaises(ValueError) as context:
            tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertIn('Expected byte-like object with length 4. ',
                      str(context.exception))

    def test_create_outpoint_no_index(self):
        outpoint_index = None
        outpoint_tx_id = helpers.outpoint_tx_id

        with self.assertRaises(ValueError) as context:
            tx.Outpoint(outpoint_tx_id, outpoint_index)

        self.assertIn('Expected byte-like object. ',
                      str(context.exception))

    def test_copy(self):
        outpoint_index = helpers.outpoint_index
        outpoint_tx_id = helpers.outpoint_tx_id

        res = tx.Outpoint(outpoint_tx_id, outpoint_index)
        copy = res.copy()
        self.assertEqual(res, copy)
        self.assertIsNot(res, copy)


class TestTxIn(unittest.TestCase):

    def setUp(self):
        outpoint_index = helpers.outpoint_index
        outpoint_tx_id = helpers.outpoint_tx_id

        self.stack_script = helpers.stack_script
        self.redeem_script = helpers.redeem_script
        self.sequence = helpers.sequence
        self.outpoint = tx.Outpoint(outpoint_tx_id, outpoint_index)

    def test_create_input(self):
        tx_in = tx.TxIn(self.outpoint, self.stack_script,
                        self.redeem_script, self.sequence)

        self.assertEqual(tx_in.outpoint, self.outpoint)
        self.assertEqual(tx_in.stack_script, self.stack_script)
        self.assertEqual(tx_in.redeem_script, self.redeem_script)
        self.assertEqual(tx_in.sequence, self.sequence)
        self.assertEqual(tx_in, helpers.tx_in)

    def test_copy(self):
        tx_in = tx.TxIn(self.outpoint, self.stack_script,
                        self.redeem_script, self.sequence)

        tx_in_copy = tx_in.copy()

        self.assertEqual(tx_in, tx_in_copy)  # They should be equal
        self.assertIsNot(tx_in, tx_in_copy)  # But not the same object

    def test_long_script_sig(self):
        with self.assertRaises(ValueError) as context:
            tx.TxIn(self.outpoint, b'\x00' * 1000,
                    b'\x00' * 1000, self.sequence)

        self.assertIn(
            'Input script_sig is too long. Expected <= 1650 bytes. '
            'Got 2000 bytes.',
            str(context.exception))


class TestTxOut(unittest.TestCase):

    def setUp(self):
        self.value = helpers.output_value_0
        self.output_script = helpers.output_script_0

    def test_create_output(self):
        tx_out = tx.TxOut(self.value, self.output_script)
        self.assertEqual(tx_out, helpers.tx_out_0)

    def test_copy(self):
        tx_out = tx.TxOut(self.value, self.output_script)
        tx_out_copy = tx_out.copy()

        self.assertEqual(tx_out, tx_out_copy)  # They should be equal
        self.assertIsNot(tx_out, tx_out_copy)  # But not the same object

    def test_dust_limit_error(self):
        with self.assertRaises(ValueError) as context:
            tx.TxOut(utils.i2le_padded(5, 8), self.output_script)

        self.assertIn(
            'Transaction value below dust limit. '
            'Expected more than 546 sat. Got: 5 sat.',
            str(context.exception))


class TestWitnessStackItem(unittest.TestCase):

    def setUp(self):
        self.stack_item_bytes = helpers.P2WSH_WITNESS_STACK_ITEMS[1]

    def test_create_stack_item(self):
        w = tx.WitnessStackItem(self.stack_item_bytes)
        self.assertEqual(w.item, self.stack_item_bytes)
        self.assertEqual(w.item_len, len(self.stack_item_bytes))
        self.assertEqual(
            w,
            bytes([len(self.stack_item_bytes)]) + self.stack_item_bytes)

    def test_from_bytes(self):
        w = tx.WitnessStackItem.from_bytes(
            bytes([len(self.stack_item_bytes)]) + self.stack_item_bytes)
        self.assertEqual(w.item, self.stack_item_bytes)
        self.assertEqual(w.item_len, len(self.stack_item_bytes))
        self.assertEqual(
            w,
            bytes([len(self.stack_item_bytes)]) + self.stack_item_bytes)


class TestInputWitness(unittest.TestCase):

    def setUp(self):
        self.stack = [tx.WitnessStackItem(b)
                      for b in helpers.P2WSH_WITNESS_STACK_ITEMS]

    def test_create_witness(self):
        iw = tx.InputWitness(self.stack)
        self.assertEqual(len(iw.stack), len(self.stack))
        for item, expected in zip(iw.stack, self.stack):
            self.assertEqual(item, expected)

        bad_stack = [None, 1]
        with self.assertRaises(ValueError) as context:
            tx.InputWitness(bad_stack)

        self.assertIn('Invalid witness stack item. Expected bytes. Got None',
                      str(context.exception))

    def test_from_bytes(self):
        iw = tx.InputWitness.from_bytes(helpers.P2WSH_WITNESS)
        self.assertEqual(len(iw.stack), len(self.stack))
        for item, expected in zip([s.item for s in iw.stack],
                                  [s.item for s in self.stack]):
            self.assertEqual(item, expected)


class TestTx(unittest.TestCase):

    def setUp(self):
        self.outpoint_index = helpers.outpoint_index
        self.outpoint_tx_id = helpers.outpoint_tx_id

        self.stack_script = helpers.stack_script
        self.redeem_script = helpers.redeem_script
        self.sequence = helpers.sequence
        self.outpoint = tx.Outpoint(self.outpoint_tx_id, self.outpoint_index)

        self.tx_in = tx.TxIn(self.outpoint, self.stack_script,
                             self.redeem_script, self.sequence)

        self.value_0 = helpers.output_value_0
        self.output_script_0 = helpers.output_script_0
        self.value_1 = helpers.output_value_1
        self.output_script_1 = helpers.output_script_1

        self.tx_out_0 = tx.TxOut(self.value_0, self.output_script_0)
        self.tx_out_1 = tx.TxOut(self.value_1, self.output_script_1)

        self.version = helpers.version
        self.none_flag = None
        self.tx_ins = [self.tx_in]
        self.tx_outs = [self.tx_out_0, self.tx_out_1]
        self.none_witnesses = None
        self.lock_time = helpers.lock_time

        self.segwit_flag = b'\x00\x01'
        self.stack = [tx.WitnessStackItem(b)
                      for b in helpers.P2WSH_WITNESS_STACK_ITEMS]
        self.tx_witnesses = [tx.InputWitness(self.stack)]

    # Convenience monotest
    # Sorta broken.
    def test_everything_witness(self):
        version = bytearray([0] * 4)
        flag = b'\x00\x01'
        outpoint_index = utils.i2le_padded(0, 4)
        outpoint_tx_id = bytearray(bytearray.fromhex(
            '10399b3f20cbdd4b5ac3f823afdba28b'
            '9f70e21437a59b312a1b62c42c5cd101'))[::-1]
        outpoint = tx.Outpoint(outpoint_tx_id, outpoint_index)

        sequence = utils.i2le_padded(0, 4)

        script = bytearray(bytearray.fromhex('473044022000e02ea97289a35181a9bfabd324f12439410db11c4e94978cdade6a665bf1840220458b87c34d8bb5e4d70d01041c7c2d714ea8bfaca2c2d2b1f9e5749c3ee17e3d012102ed0851f0b4c4458f80e0310e57d20e12a84642b8e097fe82be229edbd7dbd53920f6665740b1f950eb58d646b1fae9be28cef842da5e51dc78459ad2b092e7fd6e514c5163a914bb408296de2420403aa79eb61426bb588a08691f8876a91431b31321831520e346b069feebe6e9cf3dd7239c670400925e5ab17576a9140d22433293fe9652ea00d21c5061697aef5ddb296888ac'))  # noqa: E501

        tx_in = tx.TxIn(outpoint, script, bytearray(), sequence)
        tx_ins = [tx_in]

        tx_outs = [
            tx.TxOut(
                value=bytearray(utils.i2le_padded(2000, 8)),
                output_script=bytearray(bytearray.fromhex('76a914f2539f42058da784a9d54615ad074436cf3eb85188ac')))  # noqa: E501
        ]
        none_witnesses = [
            tx.InputWitness(
                [
                    tx.WitnessStackItem(bytearray([0x88] * 18)),
                    tx.WitnessStackItem(bytearray([0x99] * 18))
                ]
            )
        ]
        lock_time = bytearray([0xff] * 4)

        tx.Tx(version, flag, tx_ins, tx_outs, none_witnesses, lock_time)

        # TODO: needs assertions

    # Convenience monotest
    def test_everything(self):
        version = utils.i2le_padded(1, 4)
        outpoint_index = utils.i2le_padded(0, 4)
        outpoint_tx_id = bytearray(bytearray.fromhex(
            '10399b3f20cbdd4b5ac3f823afdba28b'
            '9f70e21437a59b312a1b62c42c5cd101'))[::-1]
        outpoint = tx.Outpoint(outpoint_tx_id, outpoint_index)

        sequence = utils.i2le_padded(0, 4)

        script = bytearray(bytearray.fromhex('473044022000e02ea97289a35181a9bfabd324f12439410db11c4e94978cdade6a665bf1840220458b87c34d8bb5e4d70d01041c7c2d714ea8bfaca2c2d2b1f9e5749c3ee17e3d012102ed0851f0b4c4458f80e0310e57d20e12a84642b8e097fe82be229edbd7dbd53920f6665740b1f950eb58d646b1fae9be28cef842da5e51dc78459ad2b092e7fd6e514c5163a914bb408296de2420403aa79eb61426bb588a08691f8876a91431b31321831520e346b069feebe6e9cf3dd7239c670400925e5ab17576a9140d22433293fe9652ea00d21c5061697aef5ddb296888ac'))  # noqa: E501

        tx_in = tx.TxIn(outpoint, script, bytearray(), sequence)
        tx_ins = [tx_in]

        tx_outs = [
            tx.TxOut(
                value=bytearray(utils.i2le_padded(2000, 8)),
                output_script=bytearray(bytearray.fromhex('76a914f2539f42058da784a9d54615ad074436cf3eb85188ac')))  # noqa: E501
        ]

        lock_time = utils.i2le_padded(0, 4)

        res = tx.Tx(version, None, tx_ins, tx_outs, None, lock_time)

        self.assertEqual(res.hex(), helpers.RAW_P2SH_TO_P2PKH)

    # TODO: Break up this monstrosity
    def test_create_tx(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        self.assertEqual(t, helpers.P2PKH_SPEND)

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, b'\x00\x00', self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)
        self.assertIn(
            'Invald segwit flag. Expected None or ',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, self.segwit_flag, self.tx_ins, self.tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Got segwit flag but no witnesses.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, b'\x00\x01', self.tx_ins, self.tx_outs,
                  [], self.lock_time)
        self.assertIn(
            'Got segwit flag but no witnesses.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, None, self.tx_ins, self.tx_outs,
                  self.tx_witnesses, self.lock_time)
        self.assertIn(
            'Got witnesses but no segwit flag.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            stack = self.stack + [self.stack[0]]
            witness = tx.InputWitness(stack)
            tx.Tx(self.version, self.segwit_flag, self.tx_ins, self.tx_outs,
                  witness, self.lock_time)
        self.assertIn(
            'Witness and TxIn lists must be same length. ',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx.Tx(self.version, self.segwit_flag, self.tx_ins, self.tx_outs,
                  [1 for _ in self.tx_witnesses], self.lock_time)
        self.assertIn(
            'Invalid InputWitness. Expected instance of InputWitness.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_ins = [self.tx_ins[0] for _ in range(257)]
            tx.Tx(self.version, self.none_flag, tx_ins, self.tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Too many inputs or outputs. Stop that.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_outs = [self.tx_outs[0] for _ in range(257)]
            tx.Tx(self.version, self.none_flag, self.tx_ins, tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Too many inputs or outputs. Stop that.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_ins = []
            tx.Tx(self.version, self.none_flag, tx_ins, self.tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Too few inputs or outputs. Stop that.',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_ins = [1]
            tx.Tx(self.version, self.none_flag, tx_ins, self.tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Invalid TxIn. Expected instance of TxIn. Got int',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_outs = [1]
            tx.Tx(self.version, self.none_flag, self.tx_ins, tx_outs,
                  None, self.lock_time)
        self.assertIn(
            'Invalid TxOut. Expected instance of TxOut. Got int',
            str(context.exception))

        with self.assertRaises(ValueError) as context:
            tx_in = self.tx_ins[0].copy(stack_script=b'\x00' * 1616,
                                        redeem_script=None)
            tx_ins = [tx_in for _ in range(255)]
            tx_outs = [self.tx_outs[0] for _ in range(255)]
            tx.Tx(self.version, self.none_flag, tx_ins, tx_outs,
                  None, self.lock_time)

        self.assertIn(
            'Tx is too large. Expect less than 100kB. Got: 440397 bytes',
            str(context.exception))

    def test_calc_fee(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        self.assertEqual(t.calc_fee([10 ** 8]), 57534406)

    def test_sighash_none(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        with self.assertRaises(NotImplementedError) as context:
            t.sighash_none()

        self.assertIn('SIGHASH_NONE is a bad idea.', str(context.exception))

    def test_copy(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        t_copy = t.copy()

        self.assertEqual(t, t_copy)
        self.assertIsNot(t, t_copy)

    def test_with_new_inputs(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        t_with_new_inputs = t.with_new_inputs([self.tx_ins[0]])
        t_copy = t.copy(tx_ins=self.tx_ins + [self.tx_ins[0]])

        self.assertEqual(t_copy, t_with_new_inputs)
        self.assertIsNot(t_copy, t_with_new_inputs)

    def test_with_new_outputs(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)

        t_with_new_outputs = t.with_new_outputs([self.tx_outs[0]])
        t_copy = t.copy(tx_outs=self.tx_outs + [self.tx_outs[0]])

        self.assertEqual(t_copy, t_with_new_outputs)
        self.assertIsNot(t_copy, t_with_new_outputs)

    def test_with_new_inputs_and_witnesses(self):
        new = (self.tx_ins[0], self.tx_witnesses[0])
        t = tx.Tx(self.version, self.segwit_flag, self.tx_ins, self.tx_outs,
                  self.tx_witnesses, self.lock_time)

        t_with_new = t.with_new_inputs_and_witnesses([new])
        t_copy = t.copy(tx_ins=self.tx_ins + [new[0]],
                        tx_witnesses=self.tx_witnesses + [new[1]])

        self.assertEqual(t_copy, t_with_new)
        self.assertIsNot(t_copy, t_with_new)

    def test_sighash_all(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)
        self.assertEqual(t.sighash_all(0, helpers.prevout_pk_script),
                         helpers.sighash_all)

    def test_sighash_all_anyone_can_pay(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)
        self.assertEqual(
            t.sighash_all(0, helpers.prevout_pk_script, anyone_can_pay=True),
            helpers.sighash_all_anyonecanpay)

    def test_sighash_single(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)
        self.assertEqual(t.sighash_single(0, helpers.prevout_pk_script),
                         helpers.sighash_single)

    def test_sighash_single_anyone_can_pay(self):
        t = tx.Tx(self.version, self.none_flag, self.tx_ins, self.tx_outs,
                  self.none_witnesses, self.lock_time)
        self.assertEqual(
            t.sighash_single(
                0, helpers.prevout_pk_script, anyone_can_pay=True),
            helpers.sighash_single_anyonecanpay)