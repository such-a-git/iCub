import socket
import spynnaker8 as sim
import numpy as np
#import logging
import matplotlib.pyplot as plt

from pacman.model.constraints.key_allocator_constraints import FixedKeyAndMaskConstraint
from pacman.model.graphs.application import ApplicationSpiNNakerLinkVertex
from pacman.model.routing_info import BaseKeyAndMask
from spinn_front_end_common.abstract_models.abstract_provides_n_keys_for_partition import AbstractProvidesNKeysForPartition
from spinn_front_end_common.abstract_models.abstract_provides_outgoing_partition_constraints import AbstractProvidesOutgoingPartitionConstraints
from spinn_utilities.overrides import overrides

from spinn_front_end_common.abstract_models \
    import AbstractSendMeMulticastCommandsVertex
from spinn_front_end_common.utility_models.multi_cast_command \
    import MultiCastCommand


from pyNN.utility import Timer
from pyNN.utility.plotting import Figure, Panel
from pyNN.random import RandomDistribution, NumpyRNG

from spynnaker.pyNN.models.neuron.plasticity.stdp.common import plasticity_helpers

# identifiers for edge partitions,
# RETINA_X_SIZE = 304
# RETINA_Y_SIZE = 240
# RETINA_BASE_KEY = 0x00000000
# RETINA_MASK = 0xFF000000
# FILTER_BASE_KEY = 0x01000000
# FILTER_BASE_MASK = 0xFFFFFE00
# RETINA_Y_BIT_SHIFT = 9

NUM_NEUR_IN = 72960
NUM_NEUR_OUT = 256

class ICUBInputVertex(
        ApplicationSpiNNakerLinkVertex,
        AbstractProvidesOutgoingPartitionConstraints):

    def __init__(self, spinnaker_link_id, board_address=None,
                 constraints=None, label=None):

        ApplicationSpiNNakerLinkVertex.__init__(
            self, n_atoms=NUM_NEUR_IN, spinnaker_link_id=spinnaker_link_id,
            board_address=board_address, label=label)

        AbstractProvidesNKeysForPartition.__init__(self)
        AbstractProvidesOutgoingPartitionConstraints.__init__(self)


    @overrides(AbstractProvidesOutgoingPartitionConstraints.
               get_outgoing_partition_constraints)
    def get_outgoing_partition_constraints(self, partition):
        return [FixedKeyAndMaskConstraint(
            keys_and_masks=[BaseKeyAndMask(
                base_key=0, #upper part of the key,
                mask=0xFFFFFF00)])] #256 neurons in the LSB bits ,
                #keys, i.e. neuron addresses of the input population that sits in the ICUB vertex,

class ICUBOutputVertex(ApplicationSpiNNakerLinkVertex,
                       AbstractSendMeMulticastCommandsVertex):

    def __init__(self, spinnaker_link_id, board_address=None,
                 constraints=None, label=None):

        ApplicationSpiNNakerLinkVertex.__init__(
            self, n_atoms=NUM_NEUR_OUT, spinnaker_link_id=spinnaker_link_id,
            board_address=board_address, label=label)
        AbstractSendMeMulticastCommandsVertex.__init__(self)


    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.start_resume_commands)
    def start_resume_commands(self):
        return [MultiCastCommand(
            key=0x80000000, payload=0, repeat=5, delay_between_repeats=100)]


    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.pause_stop_commands)
    def pause_stop_commands(self):
        return [MultiCastCommand(
            key=0x40000000, payload=0, repeat=5, delay_between_repeats=100)]

    @property
    @overrides(AbstractSendMeMulticastCommandsVertex.timed_commands)
    def timed_commands(self):
        return []




sim.setup(timestep=1.0)
#sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 255)

# set up populations,
pop = sim.Population(None, ICUBInputVertex(spinnaker_link_id=0), label='pop_in')

#neural population    ,
pop_DCN = sim.Population(256, sim.IF_curr_exp(), label='pop_DCN') #1DCN receives from 20PC (in biology is from 100PC),

pop_out = sim.Population(None, ICUBOutputVertex(spinnaker_link_id=0), label='pop_out')

# sim.Projection(pop, neuron_pop, sim.FixedProbabilityConnector(0.1), sim.StaticSynapse(weight=1.0))
input_proj_in2DCN = sim.Projection(pop, pop_DCN, sim.OneToOneConnector(),synapse_type=sim.StaticSynapse(weight=10, delay=1), receptor_type='excitatory'),
#input_proj_DCN2out = sim.Projection(pop_DCN, pop_out, sim.OneToOneConnector(),synapse_type=sim.StaticSynapse(weight=10, delay=1), receptor_type='excitatory'),

sim.external_devices.activate_live_output_to(pop_DCN,pop)
#sim.external_devices.activate_live_output_to(pop_DCN,pop_out)

#recordings and simulations,
# pop_DCN.record([spikes])
simtime = 6000000 #ms,
sim.run(simtime)
# neo = pop_DCN.get_data(variables=[spikes])
# spikes = neo.segments[0].spiketrains
# print spikes
#v = neo.segments[0].filter(name='v')[0],
#print v ,

sim.end()

# plot.Figure(
# # plot spikes (or in this case spike),
# plot.Panel(spikes, yticks=True, markersize=5, xlim=(0, simtime))
# plt.show()
