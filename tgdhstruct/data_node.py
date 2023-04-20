# file: DataNode.py
#
'''This file contains the DataNode class.'''

# import modules
#
from __future__ import annotations
import gc
from typing import Optional
from anytree import NodeMixin
from Crypto.Random.random import randint
from Crypto.PublicKey import RSA

# class: DataNode
#
class DataNode(NodeMixin):
    '''
    Description
    -----------
    This is the node class for use in the binary tree structure.

    Global Data
    -----------
    int: g
        The generator for Diffie-Hellman algorithm
    int: p
        The modulus for Diffie-Hellman algorithm

    Attributes
    ----------
    pos : str
        The position of the node relative to parent (left or right child)
    l : int
        The level index of the node
    v : int
        The position index of the node
    parent: DataNode
        The parent of the node
    ntype : str
        The type of the node: root, inter, mem, spon
    mid : int
        The member ID of the node
    rchild : DataNode
        The right child of the node
    lchild : DataNode
        The left child of the node
    name : str
        The level and position index of the node <l,v>
    key: int
        The private key of the node
    b_key: int
        The blind (public) key of the node

    Methods
    -------
    get_sibling(self) -> DataNode
        This method returns the sibling of any node in the binary tree.
     calculate_name(self) -> None
        This method determines the name of a node based on the name of its parent.
    gen_private_key(self) -> None
        This method generates a random private key.
    gen_blind_key(self) -> None
        This method generates the blind key.
    get_key_path(self) -> list[DataNode]
        This method gets the path from the current node up to the root.
     get_co_path(self) -> list[DataNode]
        This method gets the co-path from the current node up to the root.
    sponsor_assign(self, mid: Optional[int]=None, key: Optional[int]=None, b_key: Optional[int]=None, join: bool=True) -> None
        This method tags a node as the sponsor node.
    insertion_assign(self) -> None
        This method tags a node as the insertion node.
    new_memb_assign(self, mid: int) -> None
        This method tags a node as the new member node.
    transfer_data_remove(self, node: DataNode) -> None
        This method transfers data from a specified node and then removes that node.
    make_root(self) -> None
        This method makes the current node the root.
    print_attributes(self) -> None
        This method prints all node attributes.
    '''

    # define global Diffie-Hellman Data
    #
    #g = 5
    #p = 23
    g = 2
    p = 0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AACAA68FFFFFFFFFFFFFFFF

    # constructor
    #
    def __init__(self, pos: str='NA', l: int=0, v: int=0, parent: Optional[DataNode]=None, ntype: str='root', mid: Optional[int]=None, rchild: Optional[DataNode]=None, lchild: Optional[DataNode]=None) -> None:
        '''This is the constructor.'''

        # tree data
        #
        self.pos = pos
        self.l = l
        self.v = v
        self.parent = parent
        self.ntype = ntype
        self.mid = mid
        self.rchild = rchild
        self.lchild = lchild
        self.name = self.calculate_name()

        # Diffie-Hellman encryption data
        #
        self.key = None
        self.b_key = None
        self.rsa_pub = None
    #
    # end constructor

    # method: get_sibling
    #
    def get_sibling(self) -> DataNode:
        '''This method returns the sibling of any node in the binary tree.'''

        return self.siblings[0]
    #
    # end method: get_sibling

    # method: calculate_name
    #
    def calculate_name(self) -> None:
        '''This method determines the name of a node based on the name of its parent.'''

        if self.pos == 'left':
            self.l = self.parent.l+1
            self.v = 2*self.parent.v
            return '<' + str(self.l) + ',' + str(self.v) + '>'
        elif self.pos == 'right':
            self.l = self.parent.l+1
            self.v = 2*self.parent.v+1
            return '<' + str(self.l) + ',' + str(self.v) + '>'
        else:
            return '<' + str(self.l) + ',' + str(self.v) + '>'
    #
    # end method: calculate_name

    # method: gen_private_key
    #
    def gen_private_key(self) -> None:
        '''This method generates a random private key.'''

        #self.key = randint(1, int(DataNode.p-1))
        rsa_key_pair = RSA.generate(1024)
        public_bytes = rsa_key_pair.publickey().exportKey('DER')
        self.rsa_pub = public_bytes
        private_bytes = rsa_key_pair.exportKey('DER')
        self.key = int.from_bytes(private_bytes, "big")
    #
    # end method: gen_private_key

    # method: gen_blind_key
    #
    def gen_blind_key(self) -> None:
        '''This method generates the blind key.'''

        self.b_key = pow(DataNode.g, self.key, DataNode.p)
    #
    # end method: gen_blind_key

    # method: get_key_path
    #
    def get_key_path(self) -> list[DataNode]:
        '''This method gets the path from the current node up to the root.'''

        return(list(reversed(self.path)))
    #
    # end method: get_key_path

    # method: get_co_path
    #
    def get_co_path(self) -> list[DataNode]:
        '''This method gets the co-path from the current node up to the root.'''

        return [node.get_sibling() for node in self.get_key_path() if node.ntype != 'root']
    #
    # end method: get_co_path

    # method: sponsor_assign
    #
    def sponsor_assign(self, mid: Optional[int]=None, key: Optional[int]=None, b_key: Optional[int]=None, join: bool=True) -> None:
        '''This method tags a node as the sponsor node.'''

        self.ntype = 'spon'
        if join:
            self.mid = mid
            self.key = key
            self.b_key = b_key
    #
    # end method: sponsor_assign

    # method: insertion_assign
    #
    def insertion_assign(self) -> None:
        '''This method tags a node as the insertion node.'''

        self.ntype = 'inter'
        self.mid = None
        self.key = None
        self.b_key = None
    #
    # end method: insertion_assign

    # method: new_memb_assign
    #
    def new_memb_assign(self, mid: int) -> None:
        '''This method tags a node as the new member node.'''

        self.ntype = 'mem'
        self.mid = mid
    #
    # end method: new_memb_assign

    # method: transfer_data_remove
    #
    def transfer_data_remove(self, node: DataNode) -> None:
        '''This method transfers data from a specified node and then removes that node.'''

        self.ntype = node.ntype
        self.mid = node.mid
        self.rchild = node.rchild
        self.lchild = node.lchild
        self.children = node.children
        self.key = node.key
        self.b_key = node.b_key
        del node
        gc.collect()
    #
    # end method: transfer_data_remove

    # method: make_root
    #
    def make_root(self) -> None:
        '''This method makes the current node the root.'''

        self.pos = 'NA'
        self.ntype = 'root'
        self.mid = None
        self.parent = None
        self.l = 0
        self.v = 0
        self.name = '<0,0>'
        self.key = None
        self.b_key = None
    #
    # end method: make_root

    # method: print_attributes
    #
    def print_attributes(self) -> None:
        '''This method prints all node attributes.'''

        print(f"\n{'//'.center(80, '-')}")
        print(f"Node Name: {self.name}")
        if self.parent is not None:
            print(f"Node Parent: {self.parent.name}")
        print(f"Node index: <{str(self.l)},{str(self.v)}>")
        print(f"Node Type: {self.ntype}")
        if self.mid is not None:
            print(f"Node id: {str(self.mid)}")
        if self.lchild is not None:
            print(f"Node left child: {self.lchild.name}")
        if self.rchild is not None:
            print(f"Node right child: {self.rchild.name}")
        print(f"Private key: {str(self.key)}")
        print(f"Blind key: {str(self.b_key)}")
        print("Key path:")
        for node in self.get_key_path():
            print(node.name)
        print("Key co-path:")
        for node in self.get_co_path():
            print(node.name)
        print(f"{'//'.center(80, '-')}")
    #
    # end method: print_attributes
#
# end class: DataNode
#
# end file: DataNode.py
