#!/usr/bin/env python3
# Copyright (c) 2017-2017 The Bitcoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test getperblockstats rpc call
#
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (
    start_nodes,
    assert_equal,
    assert_raises_jsonrpc,
    connect_nodes_bi,
)

class GetperblockstatsTest(BitcoinTestFramework):

    def __init__(self):
        super().__init__()
        self.setup_clean_chain = True
        self.is_network_split = False
        self.num_nodes = 2
        self.extra_args = [
            ['-debug', '-whitelist=127.0.0.1'],
            ['-debug', '-whitelist=127.0.0.1', '-paytxfee=0.003'],
        ]

    def setup_network(self):
        self.nodes = start_nodes(self.num_nodes, self.options.tmpdir, self.extra_args)
        connect_nodes_bi(self.nodes, 0 , 1)
        self.sync_all()

    def assert_contains(self, data, values, check_cointains=True):
        for val in values:
            if (check_cointains):
                assert(val in data)
            else:
                assert(val not in data)

    def run_test(self):
        node = self.nodes[0]
        node.generate(101)

        node.sendtoaddress(address=self.nodes[1].getnewaddress(), amount=10, subtractfeefromamount=True)
        node.generate(1)
        self.sync_all()

        node_balance = node.getbalance()['bitcoin'] - 1
        node.sendtoaddress(address=node.getnewaddress(), amount=node_balance, subtractfeefromamount=True)
        node.sendtoaddress(address=node.getnewaddress(), amount=node_balance, subtractfeefromamount=True)
        self.nodes[1].sendtoaddress(address=node.getnewaddress(), amount=1, subtractfeefromamount=True)
        self.sync_all()
        node.generate(1)

        start_height = 101
        max_plot_pos = 2
        plot_data = node.getperblockstats(start=start_height, end=start_height + max_plot_pos)

        all_values = [
            'height',
            'time',
            'minfee',
            'maxfee',
            'totalfee',
            'minfeerate',
            'maxfeerate',
            'avgfee',
            'avgfeerate',
            'txs',
            'ins',
            'outs',
        ]
        self.assert_contains(plot_data, all_values)

        # The order of the data is inverted for every value
        assert_equal(plot_data['height'][max_plot_pos], start_height)
        assert_equal(plot_data['height'][0], start_height + max_plot_pos)

        assert_equal(plot_data['minfee'][max_plot_pos], 0)
        assert_equal(plot_data['maxfee'][max_plot_pos], 0)
        assert_equal(plot_data['totalfee'][max_plot_pos], 0)
        assert_equal(plot_data['minfeerate'][max_plot_pos], 0)
        assert_equal(plot_data['maxfeerate'][max_plot_pos], 0)
        assert_equal(plot_data['avgfee'][max_plot_pos], 0)
        assert_equal(plot_data['avgfeerate'][max_plot_pos], 0)
        assert_equal(plot_data['txs'][max_plot_pos], 1)
        assert_equal(plot_data['ins'][max_plot_pos], 1) # coinbase input counts
        assert_equal(plot_data['outs'][max_plot_pos], 2)

        assert_equal(plot_data['minfee'][1], 38660)
        assert_equal(plot_data['maxfee'][1], 38660)
        assert_equal(plot_data['totalfee'][1], 38660)
        assert_equal(plot_data['minfeerate'][1], 5)
        assert_equal(plot_data['maxfeerate'][1], 5)
        assert_equal(plot_data['avgfee'][1], 38660)
        assert_equal(plot_data['avgfeerate'][1], 5)
        assert_equal(plot_data['txs'][1], 2)
        assert_equal(plot_data['ins'][1], 2)
        assert_equal(plot_data['outs'][1], 5)

        assert_equal(plot_data['minfee'][0], 46500)
        assert_equal(plot_data['maxfee'][0], 532800)
        assert_equal(plot_data['totalfee'][0], 705920)
        assert_equal(plot_data['minfeerate'][0], 5)
        assert_equal(plot_data['maxfeerate'][0], 75)
        assert_equal(plot_data['avgfee'][0], 235306)
        assert_equal(plot_data['avgfeerate'][0], 16)
        assert_equal(plot_data['txs'][0], 4)
        assert_equal(plot_data['ins'][0], 104)
        assert_equal(plot_data['outs'][0], 11)

        # Test invalid parameters raise the proper json exceptions
        assert_raises_jsonrpc(-8, 'Start block height out of range', node.getperblockstats, start=-1)
        assert_raises_jsonrpc(-8, 'Start block height out of range', node.getperblockstats, start=0)
        assert_raises_jsonrpc(-8, 'End block height out of range', node.getperblockstats, start=1, end=start_height + max_plot_pos + 1)

        invalid_plot_value = 'asdfghjkl'
        assert_raises_jsonrpc(-8, 'Invalid plot value %s' % invalid_plot_value, node.getperblockstats, start=1, end=start_height + max_plot_pos, plotvalues='minfee,%s' % invalid_plot_value)
        assert_raises_jsonrpc(-8, 'Invalid plot value %s' % invalid_plot_value, node.getperblockstats, start=1, end=start_height + max_plot_pos, plotvalues='%s,minfee' % invalid_plot_value)
        assert_raises_jsonrpc(-8, 'Invalid plot value %s' % invalid_plot_value, node.getperblockstats, start=1, end=start_height + max_plot_pos, plotvalues='minfee,%s,maxfee' % invalid_plot_value)

        # Make sure only the selected plot values are included
        plot_data = node.getperblockstats(start=start_height, end=start_height + max_plot_pos, plotvalues='minfee,maxfee')
        some_values = [
            'height',
            'time',
            'minfee',
            'maxfee',
        ]
        other_values = [x for x in all_values if x not in some_values]
        self.assert_contains(plot_data, some_values)
        self.assert_contains(plot_data, other_values, False)

if __name__ == '__main__':
    GetperblockstatsTest().main()
