# file: member_agent.py
#
'''This file contains the MemberAgent class along with helper functions.'''

# import modules
#
import time
from math import floor, log
from copy import copy
from osbrain import run_nameserver
from osbrain import run_agent
from osbrain import Proxy, NSProxy, AgentAddress
from tgdhstruct.binary_tree import BinaryTree

# function: receive_bkeys
#
def receive_bkeys(agent: Proxy, message: str) -> None:
    '''This helper function processes received blind keys.'''

    agent.log_info(f"Received: {message}")
    data = message.split(':')
    newtree = agent.get_data()
    node = newtree.find_node(data[0].lstrip('<').rstrip('>'), False)
    node.b_key = int(data[1])
    agent.set_data(newtree)
#
# end function: receive_bkeys

# function: receive_tree
#
def receive_tree(agent: Proxy, tree: BinaryTree) -> None:
    '''This helper function processes received tree object.'''

    agent.log_info("Tree received!")
    agent.set_data(tree)
#
# end function: receive_tree

# function: set_data
#
def set_data(self, tree: BinaryTree) -> None:
    '''This helper function creates and sets a data attribute for the agent.'''

    self.data = tree
#
# end function: set_data

# function: get_data
#
def get_data(self) -> BinaryTree:
    '''This function returns the created data attribute for the agent.'''

    return self.data
#
# end function: set_data

# class: MemberAgent
#
class MemberAgent():
    '''
    Description
    -----------
    This class manages the multi-agent system used to faciliate the TGDH scheme.

    Attributes
    ----------
    agents : list[Proxy]
        A list of the agents
    addr : list[AgentAddress]
        A list of the addresses used for communication
    size : int
        The number of members in the group
    nodemax : int
        The maximum number of nodes in the initial tree with <size> members
    max_height : int
        The maximum height of the initial tree
    sponsor : Agent
        The sponsor agent
    new_memb : Agent
        The new member agent
    spon_id = None
        The member ID of the sponsor
    new_id = None
        The member ID of the new member
    nameserver : NSProxy
        The running nameserver

    Methods
    -------
    send_info(self, agent: Proxy, channel: str, data_message: str) -> None:
        This method sends information to a publishing channel.
    close_connections(self) -> None:
        This method closes all agent connections.
    initial_key_exchange(self) -> None:
        This method facilitates the initial key exchange algorithmically.
    join_key_exchange(self) -> None:
        This method facilitates the key exchange for a join event algorithmically.
    join_protocol(self) -> None:
        This method facilitates a new member joining the group.
    leave_key_exchange(self):
        This method the key exchange for a leave event algorithmically.
    leave_protocol(self, eid: int):
        This method facilitates a member leaving the group.
    close(self) -> None:
        This method shuts down the nameserver.
    '''

    # constructor
    #
    def __init__(self, size: int) -> None:
        '''This is the constructor.'''

        # define class data
        #
        self.agents = {}
        self.addr = {}
        self.size = size
        self.nodemax = (2*self.size)-1
        self.max_height = floor(log((self.nodemax-1),2))
        self.sponsor = None
        self.new_memb = None
        self.spon_id = None
        self.new_id = None

        # system deployment
        #
        self.nameserver = run_nameserver()

        # initialize the tree
        #
        self.initial_key_exchange()
    #
    # end constructor

    # method: send_info
    #
    def send_info(self, agent: Proxy, channel: str, data_message: str) -> None:
        '''This method sends information to a publishing channel.'''

        agent.send(channel, data_message)
    #
    # end method: send_info

    # method: close_connections
    #
    def close_connections(self) -> None:
        '''This method closes all agent connections.'''

        for agent in self.agents.items():
            agent[1].close_all()
    #
    # end method: close_connections

    # method: initial_key_exchange
    #
    def initial_key_exchange(self) -> None:
        '''This method facilitates the initial key exchange algorithmically.'''

        # print a divider
        #
        print(f"\n{'Key Exchange (Init)'.center(80, '=')}")

        # initialize all agents with their trees and co-paths
        #
        key_paths = []
        co_paths = []
        iters = [0]*self.size
        for i in range(self.size):
            mem = f'mem_{i+1}'
            self.agents[i+1] = run_agent(mem)
            self.agents[i+1].set_method(set_data, get_data)
            self.agents[i+1].set_data(BinaryTree(self.size, i+1))
            temp_key_path = []
            for node in self.agents[i+1].get_data().my_node.get_key_path():
                temp_key_path.append(node.name)
            key_paths.append(temp_key_path)
            temp_co_path = []
            for node in self.agents[i+1].get_data().my_node.get_co_path():
                temp_co_path.append(node.name)
            co_paths.append(temp_co_path)

        # pad the co-path lists to account for co-paths of varying lengths
        #
        for i in range(self.size):
            if len(co_paths[i]) < self.max_height:
                co_padding = [None]*(self.max_height-len(co_paths[i]))
                key_padding = [None]*(self.max_height-len(key_paths[i])+1)
                co_paths[i] = co_padding + co_paths[i]
                key_paths[i] = key_padding + key_paths[i]

        # perform the send-receive communication protocol
        #
        for i in range(self.max_height):

            # establish publishers (each node will publish)
            #
            self.addr = {}
            for key, agent in self.agents.items():
                mem = f'mem_{key}'
                self.addr[key] = agent.bind('PUB', alias=mem)

            # establish subscribers (proper co-path member)
            #
            for key, agent in self.agents.items():
                dest_name = co_paths[key-1][i]
                if dest_name is not None:
                    dest_node = agent.get_data().find_node(dest_name.lstrip('<').rstrip('>'), False)
                    dest_mem = dest_node.leaves[0].mid
                    agent.connect(self.addr[dest_mem], handler=receive_bkeys)

            # send blind keys for the proper node
            #
            print('')
            for key, agent in self.agents.items():
                mem = f'mem_{key}'
                key_node = key_paths[key-1][i]
                if key_node is not None:
                    blind_key = agent.get_data().find_node(key_node.lstrip('<').rstrip('>'), False).b_key
                    message = f'{key_node}:{blind_key}'
                    self.send_info(agent, mem, message)

            # calculate appropriate blind keys
            #
            time.sleep(1)
            for key, agent in self.agents.items():
                if co_paths[key-1][i] is not None:
                    newtree = agent.get_data()
                    newtree.initial_calculate_group_key(iters[key-1])
                    iters[key-1] = iters[key-1]+1
                    agent.set_data(newtree)
                    agent.get_data().tree_print()

            # close connections to prevent unnecessary sending/receiving
            #
            self.close_connections()

            # increment the level
            #
            time.sleep(1)
            print(f"\nSYS: Level {self.max_height-i} finished -- keys exchanged!")

        print("\nSYS: Tree initialization completed!")
        print("SYS: All initial members have computed the group key.")
    #
    # end method: initial_key_exchange

    # method: join_key_exchange
    #
    def join_key_exchange(self) -> None:
        '''This method facilitates the key exchange for a join event algorithmically.'''

        # print a divider
        #
        print(f"\n{'Key Exchange (Join)'.center(80, '=')}")

        # get the update paths of all members
        #
        update_paths = {}
        for key, agent in self.agents.items():
            if key not in (self.spon_id, self.new_id):
                temp_update_path = []
                for node in agent.get_data().get_update_path():
                    temp_update_path.append(node.name)
                update_paths[key] = list(reversed(temp_update_path))
            else:
                update_paths[key] = None

        # get the sponsor's key path
        #
        spon_key_path = []
        for node in self.sponsor.get_data().my_node.get_key_path():
            spon_key_path.append(node.name)

        for i in range(len(spon_key_path)-2):

            # only the sponsor will publish
            #
            mem = f'mem_{self.spon_id}'
            self.addr[self.spon_id] = self.sponsor.bind('PUB', alias=mem)

            # establish subscribers (sponsor will publish)
            #
            key_node = spon_key_path[i+1]
            for key, agent in self.agents.items():
                if update_paths[key] is not None:
                    if key_node in update_paths[key]:
                        dest_name = key_node
                        if dest_name is not None:
                            agent.connect(self.addr[self.spon_id], handler=receive_bkeys)

            # sponsor sends appropriate blind keys
            #
            blind_key = self.sponsor.get_data().find_node(key_node.lstrip('<').rstrip('>'), False).b_key
            message = f'{key_node}:{blind_key}'
            print('')
            self.send_info(self.sponsor, mem, message)

            # close connections to prevent unnecessary sending/receiving
            #
            self.close_connections()

            # increment the level
            #
            time.sleep(1)
            print(f"\nSYS: Level {self.sponsor.get_data().my_node.l-i-1} finished -- keys exchanged!")
        #
        # end method: join_key_exchange

    # method: join_protocol
    #
    def join_protocol(self) -> None:
        '''This method facilitates a new member joining the group.'''

        print(f"\n{'Join Event'.center(80, '=')}")

        # alert current members that a new member is joining; find the sponsor
        #
        for key, agent in self.agents.items():
            newtree = agent.get_data()
            newtree.join_event()
            agent.set_data(newtree)
            if agent.get_data().my_node.ntype == 'spon':
                self.sponsor = agent

        # initialize the joining member
        #
        self.new_id = self.sponsor.get_data().nextmemb-1
        mem = f'mem_{self.new_id}'
        self.agents[self.new_id] = run_agent(mem)
        self.new_memb = self.agents[self.new_id]
        self.new_memb.set_method(set_data, get_data)
        self.new_memb.set_data(None)

        # joining member subscribes to the sponsor
        #
        mem = f'mem_{self.sponsor.get_data().uid}'
        self.addr[self.sponsor.get_data().uid] = self.sponsor.bind('PUB', alias=mem)
        dest_mem = self.sponsor.get_data().uid
        self.new_memb.connect(self.addr[dest_mem], handler=receive_tree)

        # sponsor sends the tree to the joining member
        #
        self.spon_id = self.sponsor.get_data().uid
        stree = copy(self.sponsor.get_data())
        stree.my_node.key = None
        print(f"\nSYS: Member {self.sponsor.get_data().uid} is sending the tree ...\n")
        self.send_info(self.sponsor, mem, stree)

        # allow new member to update its tree
        #
        time.sleep(1)
        newtree = self.new_memb.get_data()
        newtree.new_member_protocol()
        self.new_memb.set_data(newtree)

        # close connections
        #
        self.close_connections()

        # new member shares blind key with sponsor
        #
        mem = f'mem_{self.new_memb.get_data().uid}'
        self.addr[self.new_id] = self.new_memb.bind('PUB', alias=mem)
        self.sponsor.connect(self.addr[self.new_id], handler=receive_bkeys)
        blind_key = self.new_memb.get_data().my_node.b_key
        message = f'{self.new_memb.get_data().my_node.name}:{blind_key}'
        print('')
        self.send_info(self.new_memb, mem, message)

        # allow the sponsor and new member to calculate the group key
        #
        time.sleep(1)
        newtree_s = self.sponsor.get_data()
        newtree_s.calculate_group_key()
        self.sponsor.set_data(newtree_s)
        self.sponsor.get_data().tree_print()
        newtree_n = self.new_memb.get_data()
        newtree_n.calculate_group_key()
        self.new_memb.set_data(newtree_n)
        self.new_memb.get_data().tree_print()

        # sponsor sends updated blind keys
        #
        self.join_key_exchange()

        # allow all remaining members to calculate the group key
        #
        time.sleep(1)
        for key, agent in self.agents.items():
            if key not in (self.spon_id, self.new_id):
                newtree = agent.get_data()
                newtree.calculate_group_key()
                agent.set_data(newtree)
                agent.get_data().tree_print()

        # close connections
        #
        self.close_connections()

        print("\nSYS: Tree updation completed!")
        print("SYS: All members have computed the new group key.")
    #
    # end method: join_protocol

    # method: leave_key_exchange
    #
    def leave_key_exchange(self):
        '''This method the key exchange for a leave event algorithmically.'''

        # print a divider
        #
        print(f"\n{'Key Exchange (Leave)'.center(80, '=')}")

        # get the update paths of all members
        #
        update_paths = {}
        for key, agent in self.agents.items():
            if key != self.spon_id:
                temp_update_path = []
                for node in agent.get_data().get_update_path():
                    temp_update_path.append(node.name)
                update_paths[key] = list(reversed(temp_update_path))
            else:
                update_paths[key] = None

        # get the sponsor's key path
        #
        spon_key_path = []
        for node in self.sponsor.get_data().my_node.get_key_path():
            spon_key_path.append(node.name)

        for i in range(len(spon_key_path)-1):

            # only the sponsor will publish
            #
            mem = f'mem_{self.spon_id}'
            self.addr[self.spon_id] = self.sponsor.bind('PUB', alias=mem)

            # establish subscribers (sponsor will publish)
            #
            key_node = spon_key_path[i]
            for key, agent in self.agents.items():
                if update_paths[key] is not None:
                    if key_node in update_paths[key]:
                        dest_name = key_node
                        if dest_name is not None:
                            agent.connect(self.addr[self.spon_id], handler=receive_bkeys)

            # sponsor sends appropriate blind keys
            #
            blind_key = self.sponsor.get_data().find_node(key_node.lstrip('<').rstrip('>'), False).b_key
            message = f'{key_node}:{blind_key}'
            print('')
            self.send_info(self.sponsor, mem, message)

            # close connections to prevent unnecessary sending/receiving
            #
            self.close_connections()

            # increment the level
            #
            time.sleep(1)
            print(f"\nSYS: Level {self.sponsor.get_data().my_node.l-i} finished -- keys exchanged!")
        #
    #
    # end method: leave_key_exchange

    # method: leave_protocol
    #
    def leave_protocol(self, eid: int):
        '''This method facilitates a member leaving the group.'''

        print(f"\n{'Leave Event'.center(80, '=')}")

        # remove the agent
        #
        self.agents[eid].shutdown()
        time.sleep(1)
        del self.agents[eid]
        del self.addr[eid]

        # alert current members that a member is leaving the group; find the sponsor
        #
        for key, agent in self.agents.items():
            newtree = agent.get_data()
            newtree.leave_event(eid)
            agent.set_data(newtree)
            if agent.get_data().my_node.ntype == 'spon':
                self.sponsor = agent

        # sponsor generates new keys and calculates new group key
        #
        self.spon_id = self.sponsor.get_data().uid
        print(f"\nSYS: Member {self.sponsor.get_data().uid} is generating new keys ...")
        newtree = self.sponsor.get_data()
        newtree.key_generation()
        self.sponsor.set_data(newtree)
        newtree = self.sponsor.get_data()
        newtree.calculate_group_key()
        self.sponsor.set_data(newtree)
        self.sponsor.get_data().tree_print()

        # sponsor sends updated blind keys
        #
        self.leave_key_exchange()

        # allow all remaining members to calculate the group key
        #
        time.sleep(1)
        for key, agent in self.agents.items():
            if key != self.spon_id:
                newtree = agent.get_data()
                newtree.calculate_group_key()
                agent.set_data(newtree)
                agent.get_data().tree_print()

        # close connections
        #
        self.close_connections()

        print("\nSYS: Tree updation completed!")
        print("SYS: All members have computed the new group key.")
    #
    # end method: leave_protocol

    # method: close
    #
    def close(self) -> None:
        '''This method shuts down the nameserver.'''

        # shutdown the system
        #
        print(f"\n{'Exiting Program'.center(80, '=')}\n")
        self.nameserver.shutdown()
    #
    # end method: close
#
# end class: MemberAgent
#
# end file: member_agent.py
