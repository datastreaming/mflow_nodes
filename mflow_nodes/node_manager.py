from argparse import Namespace
from collections import deque
from logging import getLogger
from queue import Queue
from threading import Event
from threading import Thread

from mflow.tools import ThroughputStatistics
from mflow_nodes.rest_api.rest_server import RestInterfacedProcess

_logger = getLogger(__name__)


class NodeManager(RestInterfacedProcess):
    """
    Wrap the processing function to allow for inter process communication.
    """

    def __init__(self, processor_function, receiver_function, initial_parameters=None, processor_instance=None,
                 data_queue_size=16):
        """
        Constructor.
        :param processor_function: Function to run the processor in a thread.
        :param receiver_function: Function to run the receiver in a thread.
        :param initial_parameters: Parameters to pass to the function at instantiation.
        :param processor_instance: Instance of the processor (for help and parameters)
        :param data_queue_size: Size of the data queue between the processor and receiver thread.
        """
        self.processor_instance = processor_instance
        self.data_queue_size = data_queue_size
        self.current_parameters = initial_parameters or {}

        self.processor_function = processor_function
        self.processor_thread = None
        self.processor_running = Event()

        self.receiver_function = receiver_function
        self.receiver_thread = None
        self.receiver_running = Event()

        self.parameter_queue = Queue()

        self.statistics_buffer = deque(maxlen=100)
        self.statistics_namespace = Namespace()
        self.statistics = ThroughputStatistics(self.statistics_buffer, self.statistics_namespace)

        # Pre-process static attributes.
        self._process_name = getattr(self.processor_instance, "__name__",
                                     self.processor_instance.__class__.__name__) \
            if self.processor_instance else "Unknown processor"

    def is_running(self):
        """
        Return the status of the process function (running or not).
        :return: True if running, otherwise False.
        """
        return (self.processor_thread and self.processor_thread.is_alive() and self.processor_running.is_set()) and \
               (self.receiver_thread and self.receiver_thread.is_alive() and self.receiver_running.is_set())

    def start(self):
        """
        Start the processing function in a new process.
        """
        # It is either restart (so, first stop) or clean the current situation up (in case one of the threads died).
        self.stop()

        _logger.debug("Starting node.")

        data_queue = Queue(maxsize=16)

        self.processor_thread = Thread(target=self.processor_function,
                                       args=(self.processor_running, self.statistics_buffer, self.statistics_namespace,
                                             self.parameter_queue, data_queue))

        self.receiver_thread = Thread(target=self.receiver_function,
                                      args=(self.receiver_running, data_queue))

        self._set_current_parameters()
        self.processor_thread.start()
        self.receiver_thread.start()

        # Both thread need to set the running event. If not, something went wrong.
        if not (self.receiver_running.wait(1) and self.processor_running.wait(1)):
            raise ValueError("An exception occurred during the startup.")

    def stop(self):
        """
        Stop the processing function process.
        """
        _logger.debug("Stopping node.")

        self.receiver_running.clear()
        self.processor_running.clear()

        if self.receiver_thread is not None:
            self.receiver_thread.join()
            self.receiver_thread = None

        if self.processor_thread is not None:
            self.processor_thread.join()
            self.processor_thread = None

    def set_parameter(self, parameter):
        """
        Pass a parameter to the processing function. It needs to be in tuple format: (name, value).
        :param parameter: Tuple of (parameter_name, parameter_value).
        :return: None.
        """
        self.current_parameters[parameter[0]] = parameter[1]
        self.parameter_queue.put(parameter)

    def _set_current_parameters(self):
        for parameter in self.current_parameters.items():
            self.set_parameter(parameter)

    def get_process_name(self):
        return self._process_name

    def get_process_help(self):
        return RestInterfacedProcess.get_process_help(self.processor_instance)

    def get_parameters(self):
        # Collect default mflow_processor parameters and update them with the user set.
        all_parameters = RestInterfacedProcess.get_parameters(self.processor_instance) \
            if self.processor_instance else {}
        all_parameters.update(self.current_parameters)

        return all_parameters

    def get_statistics(self):
        return self.statistics.get_statistics()

    def get_statistics_raw(self):
        return list(self.statistics.get_statistics_raw())
